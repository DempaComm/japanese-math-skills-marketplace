"""Source-anchored exposition passages, never a mathematical certification."""
import hashlib
import json
import corpus

PHASE_NAMES={'assumptions':'仮定・設定','goal':'目標','argument':'論証','conclusion':'結論'}
STATUS_NAMES={'explicit':'原文に明示','partly-implicit':'一部は文脈から補って整理','statement-only':'定理・補題の結論に記載'}
SCOPE_NAMES={'statement-and-proof':'主張と証明','construction-excerpt':'構成部分の抜粋','uniqueness-excerpt':'一意性部分の抜粋','closing-excerpt':'結び部分の抜粋','induction-excerpt':'帰納段階の抜粋','implication-excerpt':'一方向の含意の抜粋','equivalence-excerpt':'同値性の二方向の抜粋'}

def load():
    data=json.loads((corpus.ROOT/'proof-passages.json').read_text())
    docs={d['id']:(d,ls) for d,ls in corpus.read_docs()}
    ids=set();functions={e['id'] for e in corpus.lexicon()}
    def verify_excerpt(x,lines,lo=1,hi=None):
        if not lo<=x['start']<=x['end']<=(hi or len(lines)):raise ValueError('Invalid passage range')
        if x['raw']!='\n'.join(lines[x['start']-1:x['end']]):raise ValueError('Passage/source mismatch')
    for p in data['passages']:
        if not all(isinstance(p.get(k),str) and p[k].strip() for k in ['use_when','prerequisites','explain']):raise ValueError('Missing reading guidance')
        if p['id'] in ids:raise ValueError('Duplicate passage ID')
        ids.add(p['id']);d,lines=docs[p['document']]
        for key in ['sha256','file','url','page_url','tier','subjects']:
            if p[key]!=d[key]:raise ValueError('Stale passage source metadata: '+p['id'])
        if not set(p['functions'])<=functions:raise ValueError('Unknown function')
        if p['scope_kind'] not in SCOPE_NAMES:raise ValueError('Unknown passage scope')
        verify_excerpt(p,lines)
        if hashlib.sha256(p['raw'].encode()).hexdigest()!=p['excerpt_sha256']:raise ValueError('Excerpt hash mismatch')
        if [x['role'] for x in p['phases']]!=list(PHASE_NAMES):raise ValueError('Missing/duplicate phases')
        for phase in p['phases']:
            if phase['explicitness'] not in STATUS_NAMES or not phase['excerpts']:raise ValueError('Invalid phase annotation')
            for x in phase['excerpts']:verify_excerpt(x,lines,p['start'],p['end'])
        for dep in p['dependencies']:verify_excerpt(dep,lines)
    guide=json.loads((corpus.ROOT/'argument-guide.json').read_text())
    categories=guide['categories']; kinds=[c['id'] for c in categories]
    if len(kinds)!=len(set(kinds)):raise ValueError('Duplicate argument kind')
    for c in categories:
        refs=[c['lead'],*c['related']]
        if len(refs)!=len(set(refs)) or not set(refs)<=ids:raise ValueError('Invalid guide references')
    for p in data['passages']:
        expected=[c['id'] for c in categories if p['id'] in [c['lead'],*c['related']]]
        if not expected or p.get('argument_kinds')!=expected:raise ValueError('Stale argument classification')
    return data['passages']

def search(query=None,identifier=None,tier='all',function=None,document=None,subject=None,kind=None):
    out=[]
    for p in load():
        if identifier and identifier!=p['id']:continue
        if tier!='all' and tier!=p['tier']:continue
        if function and function not in p['functions']:continue
        if document and document!=p['document']:continue
        if subject and subject not in p['subjects']:continue
        if kind and kind not in p['argument_kinds']:continue
        text=' '.join([p['title'],p['summary'],p['raw'],p['use_when'],p['prerequisites'],p['explain']]+[x['commentary'] for x in p['phases']])
        if query and corpus.normalize(query) not in corpus.normalize(text):continue
        out.append(p)
    return out

def markdown():
    ps=load()
    lines=['# 証明の運びを読む用例集','', '原文のまとまりと編集上の解説を分けて読む。仮定・目標・論証・結論は読解の整理であり、四段落の執筆形式を強制するものではない。','', '全文の証明と、一部の構成・一意性・結びの抜粋を区別する。省略された段階を原文の引用であるかのように補わない。各例の「そのまま移さない点」と依存先も確認する。','', '[目的別の案内](argument-guide.md) ／ [機械可読データ](proof-passages.json) ／ [ブラウザで読む](http://127.0.0.1:8769/?evidence=passages)','']
    lines += [f"- [{p['id']} {p['title']}](#{p['id'].lower()}) — {SCOPE_NAMES[p['scope_kind']]}" for p in ps]
    for p in ps:
        lines += ['',f'<a id="{p["id"].lower()}"></a>',f'## {p["id"]} {p["title"]}','',f"出典：[ {p['source_title']} ]({p['url']})、[原TeX {p['start']}–{p['end']}行]({p['file']})。採録範囲：{SCOPE_NAMES[p['scope_kind']]}。",'',p['summary'],'','### 各段階の対応（編集注）','']
        for ph in p['phases']:
            ranges='、'.join(f"{x['start']}–{x['end']}行" for x in ph['excerpts'])
            lines += [f"- **{PHASE_NAMES[ph['role']]}**：{ph['commentary']}〔{STATUS_NAMES[ph['explicitness']]}、{ranges}〕"]
        lines += ['','### 参考にする運び','']+['- '+x for x in p['lessons']]
        lines += ['','### 執筆で使うとき','',f"- 使う場面：{p['use_when']}",f"- 必要な前提：{p['prerequisites']}",f"- 説明を補う点：{p['explain']}"]
        lines += ['','### そのまま移さない点','']+['- '+x for x in p['cautions']]
        lines += ['','### 原文（無改変）','','```tex',p['raw'],'```']
        if p['dependencies']:
            lines += ['','### 前後の依存先','']
            for dep in p['dependencies']:
                lines += [f"- {dep['commentary']}（同じ文書の {dep['start']}–{dep['end']}行）"]
        lines += ['',p['review_scope']]
    return '\n'.join(lines)+'\n'

def guide_markdown():
    ps={p['id']:p for p in load()}
    guide=json.loads((corpus.ROOT/'argument-guide.json').read_text())
    lines=['# 証明の目的から用例を選ぶ','',guide['scope'],'',
           'まず目的を一つ選び、入口の例の「使う場面・必要な前提・説明を補う点」を読む。近い例は違いを比べるために使い、件数や年代を推奨の強さとしない。原文に省略や不一致がある例は注意欄を含めて読む。','',
           '| 目的 | 最初に読む例 | 比較する例 |','|---|---|---|']
    def link(id):return f'[{id}](proof-passages.md#{id.lower()})'
    for c in guide['categories']:lines.append(f"| [{c['title']}](#{c['id']}) | {link(c['lead'])} | {', '.join(link(i) for i in c['related']) or '—'} |")
    for c in guide['categories']:
        lines += ['',f'<a id="{c["id"]}"></a>',f"## {c['title']}",'',c['use_when'],'',
                  f"- 前提：{c['prerequisites']}",f"- 補う説明：{c['explain']}",f"- 選び分け：{c['distinction']}",'']
        for id in [c['lead'],*c['related']]:lines.append(f"- {link(id)} {ps[id]['title']} — {ps[id]['use_when']}")
    lines += ['','## 整理した範囲','',
              '179ファイルの検索候補と既存用例を照合し、14の目的に21例を割り当てた。既存18例に、局所有限な和、コンパクト性による有限化、選択への独立性の一部確認を補った。',
              '同じ用例を複数の目的へ案内しても、独立した別用例として数えない。写像の帰納的構成と定義の正当性、ノルムの同値と命題の同値、一様収束と単なる各点収束を区別した。',
              '超限帰納法・測度論固有の極限定理・図式追跡などの専門的な運びを網羅した案内ではない。原文の証明の正しさや、今回読んでいない依存定理の証明を認証しない。','',
              '```sh','python3 scripts/corpus.py --argument-guide','python3 scripts/corpus.py --passages --kind compactness --tier all','```','']
    return '\n'.join(lines)

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--check',action='store_true');args=a.parse_args()
    dest=corpus.ROOT/'proof-passages.md';text=markdown()
    if args.check:
        if not dest.exists() or dest.read_text()!=text:raise SystemExit('Stale proof-passages.md')
    else:dest.write_text(text)
    print(f'{len(load())} passages verified')
