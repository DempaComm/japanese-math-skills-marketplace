#!/usr/bin/env python3
"""Search pinned mathematical TeX without executing it. Standard library only."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / 'references'
SKIP = {'comment', 'verbatim', 'verbatim*', 'lstlisting', 'thebibliography'}
ROLES = {'proof':'proof','thm':'theorem','theorem':'theorem','prop':'theorem','proposition':'theorem','lem':'theorem','lemma':'theorem','cor':'theorem','corollary':'theorem','df':'definition','definition':'definition','defn':'definition','exam':'example','example':'example','rmk':'remark','remark':'remark','cau':'remark','claim':'claim'}

def read_docs():
    docs = json.loads((ROOT/'corpus-manifest.json').read_text())['documents']
    seen = set()
    result = []
    for d in docs:
        if d['id'] in seen:
            raise ValueError('Duplicate document: '+d['id'])
        seen.add(d['id'])
        p = (ROOT/d['file']).resolve()
        if not p.is_relative_to(ROOT.resolve()):
            raise ValueError('Corpus path outside references')
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != d['sha256']:
            raise ValueError('SHA mismatch: '+d['id'])
        result.append((d, raw.decode('utf-8').splitlines()))
    return result

def uncomment(s):
    for i,c in enumerate(s):
        if c == '%' and (len(s[:i])-len(s[:i].rstrip('\\'))) % 2 == 0:
            return s[:i]
    return s

def normalize(s):
    # Join source line wraps; retain ASCII word boundaries and all TeX commands.
    return re.sub(r'\s+', lambda m: ' ' if m.start()>0 and m.end()<len(s) and s[m.start()-1].isascii() and s[m.end()].isascii() else '', s).strip()

def units(lines):
    """Approximate sentence/structural units, carrying exact source line bounds.

    No macro expansion; roles derive from standard environments, not semantics.
    Punctuation inside $...$ or display environments is not a sentence boundary.
    """
    active=False; skip=None; stack=[]; section=''; label=None
    buf=[]; first=None; last=None; math=False; display=False
    def flush():
        nonlocal buf, first, last
        if not buf:return None
        text=normalize(''.join(buf));buf=[]
        u=dict(start=first,end=last,text=text,section=section,label=label,
               role=next((ROLES[x.rstrip('*')] for x in reversed(stack) if x.rstrip('*') in ROLES),'prose'))
        first=None;last=None
        return u if text else None
    for n,raw in enumerate(lines,1):
        if skip:
            if r'\end{'+skip+'}' in raw:skip=None
            continue
        s=uncomment(raw)
        if not active:
            if r'\begin{document}' not in s:continue
            active=True;s=s.split(r'\begin{document}',1)[1]
        if r'\end{document}' in s:
            s=s.split(r'\end{document}',1)[0]
            if s.strip():buf.append(s);first=first or n;last=n
            u=flush()
            if u:yield u
            return
        m=re.search(r'\\begin\{([^}]+)\}',s)
        if m and m[1] in SKIP:
            u=flush()
            if u:yield u
            if r'\end{'+m[1]+'}' not in s:skip=m[1]
            continue
        sec=re.search(r'\\(?:sub)*section\*?(?:\[[^]]*\])?\{([^}]+)\}',s)
        if sec:
            u=flush()
            if u:yield u
            section=sec[1];label=None
            continue
        if not s.strip():
            if not math and not display:
                u=flush()
                if u:yield u
            continue
        # Standalone metadata/rendering commands are not prose examples.
        if re.match(r'^\s*\\(?:maketitle|tableofcontents|bibliography|bibliographystyle|printbibliography|author|title|date)\b',s):continue
        # The environment tokens are boundaries; content on either side is retained.
        chunks=re.split(r'(\\(?:begin|end)\{[^}]+\})',s)
        for part in chunks:
            env=re.fullmatch(r'\\(begin|end)\{([^}]+)\}',part)
            if env:
                kind,name=env.groups()
                if name.rstrip('*') in {'equation','align','gather','multline','displaymath'}:
                    display=kind=='begin'
                    buf.append(part);first=first or n;last=n
                else:
                    u=flush()
                    if u:yield u
                    if kind=='begin':stack.append(name)
                    elif name in stack:stack=stack[:len(stack)-1-stack[::-1].index(name)]
                continue
            found=re.search(r'\\label\{([^}]+)\}',part)
            if found:label=found[1]
            for i,c in enumerate(part):
                escaped=(len(part[:i])-len(part[:i].rstrip('\\')))%2==1
                if c=='$' and not escaped:math=not math
                if c=='[' and i and part[i-1]=='\\':display=True
                if c==']' and i and part[i-1]=='\\':display=False
                first=first or n;last=n;buf.append(c)
                if c in '。．' and not math and not display:
                    u=flush()
                    if u:yield u
        if buf:buf.append('\n')
    u=flush()
    if u:yield u

def body(lines):
    # Compatibility for downstream callers; text is now sentence-normalized.
    for u in units(lines):yield u['start'],u['text']

def lexicon():
    return json.loads((ROOT/'lexicon.json').read_text())['entries']

def query_forms(term):
    groups=json.loads((ROOT/'search-aliases.json').read_text())['groups']
    key=normalize(term).casefold()
    for group in groups:
        if any(normalize(f).casefold()==key for f in group['forms']):
            return group['forms']
    return [term]


def search(term=None,tier='primary',limit=6,context=3,role=None,document=None,subject=None,per_document=2,forms=None,patterns=None,exclude_patterns=None,variants=False):
    queries=forms or (query_forms(term) if variants and term else [term])
    if not all(queries):raise ValueError('Empty query')
    buckets=[]
    for d,lines in reversed(read_docs()):
        if tier!='all' and d['tier']!=tier:continue
        if document and d['id']!=document:continue
        if subject and subject not in d.get('subjects',[]):continue
        hits=[]
        for u in units(lines):
            if role and role!=u['role']:continue
            matched=[q for q in queries if (normalize(q).casefold() in u['text'].casefold() if variants and len(queries)>1 else normalize(q) in u['text'])]
            if patterns:matched=[pattern for pattern in patterns if re.search(pattern,u['text'])]
            if any(re.search(pattern,u['text']) for pattern in (exclude_patterns or [])):continue
            if not matched:continue
            lo=max(1,u['start']-context);hi=min(len(lines),u['end']+context)
            hits.append(dict(document=d['id'],title=d['title'],tier=d['tier'],subjects=d.get('subjects',[]),url=d['url'],sha256=d['sha256'],file=d['file'],line=u['start'],start=lo,end=hi,match_start=u['start'],match_end=u['end'],section=u['section'],label=u['label'],role=u['role'],matched=matched,text=u['text'],fragment='\n'.join(lines[lo-1:hi]),evidence='automatic-candidate'))
        # Prefer concise, inspectable matches. Per-document cap prevents domination.
        hits.sort(key=lambda h:(len(h['text'])>1000,len(h['text'])<12,len(h['text']),h['line']))
        if hits:buckets.append(hits[:per_document])
    result=[]
    seen_text=set()
    for j in range(per_document):
        for b in buckets:
            if j<len(b):
                key=b[j]['text']
                if key in seen_text:continue
                seen_text.add(key);result.append(b[j])
            if len(result)>=limit:return result
    return result

def statistics():
    terms=list(dict.fromkeys(f for e in lexicon() for f in e['forms']))
    result={}
    for tier in ['primary','historical']:
        texts=['\n'.join(u['text'] for u in units(ls)) for d,ls in read_docs() if d['tier']==tier]
        total=len(texts)
        result[tier]={'document_count':total,'terms':{t:{'occurrences':sum(s.count(t) for s in texts),'documents':sum(t in s for s in texts),'document_fraction':round(sum(t in s for s in texts)/total,4) if total else 0} for t in terms}}
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('query',nargs='?');p.add_argument('--tier',choices=['primary','historical','all'],default='primary')
    p.add_argument('--limit',type=int,default=6);p.add_argument('--context',type=int,default=3)
    p.add_argument('--role',choices=sorted(set(ROLES.values())|{'prose'}));p.add_argument('--document');p.add_argument('--subject')
    p.add_argument('--argument-guide',action='store_true');p.add_argument('--kind');p.add_argument('--passages',action='store_true');p.add_argument('--passage')
    p.add_argument('--literal',action='store_true',help='Do not expand registered search aliases');p.add_argument('--curated',action='store_true')
    p.add_argument('--per-document',type=int,default=2);p.add_argument('--function',dest='function_id')
    p.add_argument('--verify',action='store_true');p.add_argument('--stats',action='store_true');p.add_argument('--functions',action='store_true')
    a=p.parse_args()
    if a.limit<1 or a.context<0 or a.per_document<1:p.error('limit and per-document >= 1; context >= 0')
    docs=read_docs()
    if a.argument_guide:
        import proof_passages
        proof_passages.load()
        print((ROOT/'argument-guide.json').read_text());return
    if a.kind and not (a.passages or a.passage):p.error('--kind requires --passages or --passage')
    if a.passages or a.passage:
        import proof_passages
        if a.kind and a.kind not in [c["id"] for c in json.loads((ROOT/"argument-guide.json").read_text())["categories"]]:p.error("Unknown kind; use --argument-guide")
        out=proof_passages.search(a.query,a.passage,a.tier,a.function_id,a.document,a.subject,a.kind)
        print(json.dumps(out[:a.limit],ensure_ascii=False,indent=2));return
    if a.verify:out={'verified_documents':len(docs),'bytes':sum((ROOT/d['file']).stat().st_size for d,_ in docs)}
    elif a.functions:out=[{'id':e['id'],'role':e['role'],'forms':e['forms']} for e in lexicon()]
    elif a.stats:out=statistics()
    else:
        entry=next((e for e in lexicon() if e['id']==a.function_id),None) if a.function_id else None
        if a.function_id and not entry:p.error('Unknown function; use --functions')
        if not a.query and not entry:p.error('query or --function required')
        if a.query and entry:p.error('choose query or --function')
        if a.curated:
            if not entry:p.error('--curated requires --function')
            out=[h for h in entry['curated_examples'] if (a.tier=='all' or h['tier']==a.tier) and (not a.role or h['role']==a.role) and (not a.document or h['document']==a.document) and (not a.subject or a.subject in h['subjects'])][:a.limit]
            print(json.dumps(out,ensure_ascii=False,indent=2));return
        out=search(a.query,a.tier,a.limit,a.context,a.role,a.document,a.subject,a.per_document,entry['forms'] if entry else None,entry.get('patterns') if entry else None,entry.get('exclude_patterns') if entry else None,variants=bool(a.query and not a.literal))
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
