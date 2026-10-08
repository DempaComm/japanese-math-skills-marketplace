import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import corpus

class AliasTests(unittest.TestCase):
    def test_real_lookup_and_exact_fallback(self):
        broad=corpus.search('1の分割',tier='primary',variants=True)
        self.assertTrue(broad)
        self.assertTrue(any('単位の分割' in h['matched'] for h in broad))
        self.assertEqual(corpus.search('1の分割',tier='primary'),[])
        self.assertTrue(corpus.search('1の分割',tier='historical'))
    def test_no_semantic_or_partial_expansion(self):
        self.assertEqual(corpus.query_forms('点有限'),['点有限'])
        self.assertEqual(corpus.query_forms('単位の分割について'),['単位の分割について'])
        self.assertIn('単位の分割',corpus.query_forms('Partition of Unity'))
