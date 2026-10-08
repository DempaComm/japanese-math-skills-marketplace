"""Build local viewer data from verified corpus; original TeX is never changed."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/write-japanese-math/scripts'))
import corpus
import proof_passages

def build():
    docs=[]
    for d,lines in corpus.read_docs():
        docs.append({**{k:d[k] for k in ('id','title','tier','subjects','url','page_url','sha256')},'lines':lines,'units':list(corpus.units(lines))})
    payload={'search_aliases':json.loads((corpus.ROOT/'search-aliases.json').read_text()),'schema_version':1,'documents':docs,'lexicon':corpus.lexicon(),'proof_passages':proof_passages.load(),'argument_guide':json.loads((corpus.ROOT/'argument-guide.json').read_text())}
    dest=Path(__file__).parent/'dist/corpus-data.json'
    dest.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
    print(f'{len(docs)} documents, {sum(len(d["units"]) for d in docs)} passages → {dest}')
if __name__=='__main__':build()
