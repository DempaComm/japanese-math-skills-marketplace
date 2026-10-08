#!/usr/bin/env python3
"""Rebuild/check derived corpus resources. Does not modify source snapshots."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import corpus

def encoded(data):return json.dumps(data,ensure_ascii=False,indent=2)+'\n'

def products():
    docs=corpus.read_docs(); entries=corpus.lexicon(); candidates={}
    by_id={d['id']:(d,lines) for d,lines in docs}
    for e in entries:
        for h in e['curated_examples']:
            d,lines=by_id[h['document']]
            if h['sha256']!=d['sha256'] or h['fragment']!='\n'.join(lines[h['start']-1:h['end']]):
                raise ValueError('Stale curated excerpt: '+e['id'])
        candidates[e['id']]=corpus.search(forms=e['forms'],patterns=e.get('patterns'),exclude_patterns=e.get('exclude_patterns'),tier='all',limit=12,per_document=1,context=5)
    coverage=[]; repeats=defaultdict(set)
    for d,lines in docs:
        us=list(corpus.units(lines));roles=Counter(u['role'] for u in us)
        for u in us:
            if len(u['text'])>=60:repeats[u['text']].add(d['id'])
        coverage.append({'id':d['id'],'title':d['title'],'tier':d['tier'],'subjects':d['subjects'],'source_lines':len(lines),'units':len(us),'structural_roles':dict(roles)})
    overlap=[{'text_sha256':hashlib.sha256(t.encode()).hexdigest(),'documents':sorted(ids),'characters':len(t)} for t,ids in repeats.items() if len(ids)>1]
    overview={'schema_version':2,'documents':coverage,'subjects':dict(Counter(s for d,_ in docs for s in d['subjects'])),'tiers':dict(Counter(d['tier'] for d,_ in docs)),'function_count':len(entries),'curated_examples':sum(len(e['curated_examples']) for e in entries),'automatic_candidates':sum(map(len,candidates.values())),'shared_units':sorted(overlap,key=lambda x:x['text_sha256']),'limitations':['All pinned public TeX; non-TeX sources excluded; two empty bodies','Repeated text is not independent style evidence','Structural roles and sentence splits are approximate','No TeX macro/conditional expansion or mathematical verification']}
    md=['# 文脈別の日本語表現','', '数学的な役割から表現を選ぶための辞書。候補は自動抽出、確認例は執筆エージェントが前後の文章で用法を確認したもの。著者による承認や数学的正しさの検証を意味しない。','', '各項目の「作例」は新作であり原文引用ではない。原文のコピーではなく、役割を保って自分の記号・仮定に合わせる。','', '[機械可読辞書](lexicon.json) ／ [自動候補](corpus-examples.json) ／ [集計](corpus-counts.json) ／ [分野と重複](corpus-coverage.json)','', '## 項目一覧','']
    md += [f"- [{e['role']}](#{e['id']}) — `{' / '.join(e['forms'])}`" for e in entries]
    for e in entries:
        md.extend(['',f'<a id="{e["id"]}"></a>',f'## {e["role"]} — `{e["id"]}`','',f"表現候補：{'、'.join(e['forms'])}",'',e['use_when']+'。'+e['do_not_replace_when']+'。','',f"作例（原文引用ではない）：{e['composed_example']}",''])
        if not e['curated_examples']:md.append('確認済み用例なし。'+e.get('evidence_note','自動候補を前後の文脈で確認する。'))
        for h in e['curated_examples']:
            md.extend([f"確認例：[{h['title']}]({h['url']})、[原TeX {h['match_start']}–{h['match_end']}行]({h['file']})。",'', '```tex', '\n'.join(by_id[h['document']][1][h['match_start']-1:h['match_end']]), '```','',h['review_note']])
    catalog=['# 採録範囲','', '分野タグは複数選択可。年代は著者の現在の好みの順位ではない。公開登録された179のTeXを収録。178ファイルは無改変、1ファイルは公開前に個人情報を含むコメント1行を空行に置換した。加工内容と取得原文・公開用コピーのハッシュはマニフェストに記録している。うち32件は公開URLから取得して照合し、追加147件はローカルの公開登録とハッシュを照合して取得した。本文が空の2件も原文として保持する。','', '|文書|区分|分野|抽出単位数|','|---|---|---|---|']
    catalog += [f"|[{d['title']}]({d['page_url']})|{d['tier']}|{', '.join(d['subjects'])}|{c['units']}|" for (d,_),c in zip(docs,coverage)]
    catalog += ['',f"同一の正規化本文（60文字以上）が複数文書に現れる単位は {len(overlap)} 件。用例の繰り返しを独立した支持として数えない。検索結果では完全一致する正規化本文を重複排除する。",'', 'サイト内の全数学文書を網羅していない。年代別・分野別の語数を比較して普遍的な文体規則を推定しない。']
    import proof_passages
    return {'argument-guide.md':proof_passages.guide_markdown(),'proof-passages.md':proof_passages.markdown(),'corpus-examples.json':encoded(candidates),'corpus-counts.json':encoded(corpus.statistics()),'corpus-coverage.json':encoded(overview),'lexicon.md':'\n'.join(md)+'\n','corpus-catalog.md':'\n'.join(catalog)+'\n'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    stale=[]
    for name,text in products().items():
        dest=corpus.ROOT/name
        if a.check:
            if not dest.exists() or dest.read_text()!=text:stale.append(name)
        else:dest.write_text(text)
    if stale:raise SystemExit('Stale derived files: '+', '.join(stale))
    print('Derived corpus files '+('verified' if a.check else 'rebuilt'))
if __name__=='__main__':main()
