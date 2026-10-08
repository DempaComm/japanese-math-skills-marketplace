import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('corpus',Path(__file__).parents[1]/'corpus.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

@contextlib.contextmanager
def fixture(texts):
    old=c.ROOT
    with tempfile.TemporaryDirectory() as tmp:
        c.ROOT=Path(tmp);docs=[]
        for i,text in enumerate(texts):
            p=c.ROOT/f'{i}.tex';p.write_text(text)
            docs.append(dict(id=str(i),file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),tier='primary',subjects=['algebra'],title=f'Doc {i}',url='https://example.invalid/'+str(i)))
        (c.ROOT/'corpus-manifest.json').write_text(json.dumps({'documents':docs}))
        try:yield c.ROOT
        finally:c.ROOT=old

class CorpusTests(unittest.TestCase):
    def test_crossline_and_source_mapping(self):
        text='\\begin{document}\n任意\nの$x$について\n成り立つ．\n\\end{document}'
        with fixture([text]):
            h=c.search('任意の',context=0)[0]
            self.assertEqual((h['match_start'],h['match_end']),(2,4))
            self.assertEqual(h['fragment'],'任意\nの$x$について\n成り立つ．')
    def test_exclusions(self):
        text=r'''秘密
\begin{document}
% 秘密
\begin{comment}
\end{document}
秘密
\end{comment}
\begin{verbatim}
秘密
\end{verbatim}
可視である．
\begin{thebibliography}{9}
秘密
\end{thebibliography}
\end{document}'''
        with fixture([text]):
            self.assertFalse(c.search('秘密'))
            self.assertTrue(c.search('可視'))
    def test_inline_environment_roles(self):
        us=list(c.units([r'\begin{document}',r'\begin{df}定義である．\end{df}',r'\begin{proof}証明する．\end{proof}',r'\end{document}']))
        self.assertEqual([u['role'] for u in us],['definition','proof'])
    def test_punctuation_inside_math(self):
        us=list(c.units([r'\begin{document}',r'$\text{．}$を定める．次に示す．',r'\end{document}']))
        self.assertEqual(len(us),2)
    def test_percent_escape(self):
        self.assertEqual(c.uncomment(r'A\% B% hidden'),r'A\% B')
        self.assertEqual(c.uncomment(r'A\\% hidden'),r'A\\')
    def test_dedup_and_document_filter(self):
        t='\\begin{document}\n任意の元を取る．\n\\end{document}'
        with fixture([t,t]):
            self.assertEqual(len(c.search('任意')),1)
            self.assertEqual(c.search('任意',document='0')[0]['document'],'0')
            self.assertFalse(c.search('任意',subject='analysis'))
    def test_function_false_positive(self):
        t='\\begin{document}\n帰納法によって示す．\nよって等しい．\n\\end{document}'
        with fixture([t]):
            hs=c.search(forms=['よって'],patterns=[r'(?<!に)よって'])
            self.assertEqual(len(hs),1);self.assertEqual(hs[0]['text'],'よって等しい．')
    def test_hash_failure_before_partial_output(self):
        with fixture(['\\begin{document}\n可視．\n\\end{document}']*2) as r:
            (r/'1.tex').write_text('changed')
            with self.assertRaises(ValueError):c.search('可視',limit=1)
    def test_traversal_rejected(self):
        with fixture(['x']) as r:
            m=json.loads((r/'corpus-manifest.json').read_text());m['documents'][0]['file']='../escape.tex'
            (r/'corpus-manifest.json').write_text(json.dumps(m))
            with self.assertRaises(ValueError):c.read_docs()
    def test_real_examples(self):
        docs={d['id']:(d,ls) for d,ls in c.read_docs()}
        for e in c.lexicon():
            self.assertFalse(any(ord(x)<32 for x in e['composed_example']))
            for h in e['curated_examples']:
                d,ls=docs[h['document']]
                self.assertEqual(d['sha256'],h['sha256'])
                self.assertEqual(h['fragment'],'\n'.join(ls[h['start']-1:h['end']]))
                self.assertTrue(any(u['start']==h['match_start'] and u['end']==h['match_end'] and u['text']==h['text'] for u in c.units(ls)))

if __name__=='__main__':unittest.main()
