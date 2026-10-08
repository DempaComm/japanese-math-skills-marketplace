import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
import corpus
import proof_passages

class ProofPassageTests(unittest.TestCase):
    def test_complete_source_validation(self):
        ps=proof_passages.load()
        self.assertGreaterEqual(len(ps),13)
        self.assertTrue(any(p['scope_kind']!='statement-and-proof' for p in ps))
        self.assertTrue(any(ph['explicitness']!='explicit' for p in ps for ph in p['phases']))
    def test_filter_combinations(self):
        p=proof_passages.search(identifier='JP-P08')[0]
        self.assertEqual(p['document'],'2026-04-21-01')
        result=proof_passages.search(function='reduction',tier='all')
        self.assertTrue(all('reduction' in p['functions'] for p in result))
        self.assertEqual(proof_passages.search(identifier='not-an-id'),[])
    def test_query_in_annotation(self):
        self.assertTrue(proof_passages.search(query='格子'))
    def test_guide_covers_passages_and_filters_by_purpose(self):
        guide=json.loads((corpus.ROOT/'argument-guide.json').read_text())
        passages=proof_passages.load()
        covered=set()
        for category in guide['categories']:
            expected={category['lead'],*category['related']}
            self.assertEqual({p['id'] for p in proof_passages.search(kind=category['id'])},expected)
            covered.update(expected)
        self.assertEqual(covered,{p['id'] for p in passages})
        self.assertTrue(proof_passages.search(query='局所有限',kind='well-defined'))
    def test_new_argument_forms_and_scopes(self):
        expected = [('induction','JP-P14','induction-excerpt'),
                    ('case','JP-P15','closing-excerpt'),
                    ('limit','JP-P16','implication-excerpt'),
                    ('estimate','JP-P17','statement-and-proof'),
                    ('equivalence','JP-P18','equivalence-excerpt')]
        for function, identifier, scope in expected:
            results = proof_passages.search(function=function, tier='all')
            passage = next(p for p in results if p['id']==identifier)
            self.assertEqual(passage['scope_kind'],scope)
            self.assertTrue(passage['dependencies'])
            self.assertTrue(passage['cautions'])
    def test_reject_stale_annotation_quote(self):
        old=corpus.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)
            for p in old.iterdir():
                if p.name!='proof-passages.json':(dst/p.name).symlink_to(p,target_is_directory=p.is_dir())
            # Keep sources inside allowed root using actual copies, not symlinks.
            (dst/'corpus').unlink();(dst/'corpus').mkdir()
            import shutil
            for p in (old/'corpus').iterdir():shutil.copyfile(p,dst/'corpus'/p.name)
            data=json.loads((old/'proof-passages.json').read_text())
            data['passages'][0]['phases'][0]['excerpts'][0]['raw']='not the source'
            (dst/'proof-passages.json').write_text(json.dumps(data))
            corpus.ROOT=dst
            try:
                with self.assertRaisesRegex(ValueError,'Passage/source mismatch'):proof_passages.load()
            finally:corpus.ROOT=old

if __name__=='__main__':unittest.main()
