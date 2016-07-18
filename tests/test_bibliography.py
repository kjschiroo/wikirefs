import unittest
from wikirefs.bibliography import Bibliography
import mwparserfromhell as mwp


class TestBibliography(unittest.TestCase):

    def test_refs(self):
        text = (
            "<ref name='foo'> {{cite news}} </ref>\n"
            "<ref name='foo'/>\n"
            "{{cite news}}\n"
            "{{cite other}}\n"
            "<ref name='bar'> {{cite bar}} </ref>\n"
        )
        wc = mwp.parse(text)

        blg = Bibliography(wc)
        refs = blg.refs()

        self.assertEqual(len(refs), 3)
        valid_counts = {'{{cite news}}': 3,
                        '{{cite other}}': 1,
                        '{{cite bar}}': 1}
        for r in refs:
            self.assertEqual(valid_counts[r['ref']], r['count'])


if __name__ == '__main__':
    unittest.main()
