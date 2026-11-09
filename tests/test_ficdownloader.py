"""AO3 stories saved by ficdownloader (its labelled "About" page)."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'calibre_stub'))
sys.path.insert(0, str(HERE.parent))
from extract_epub_metadata.mapping import extract_fields  # noqa: E402

CASES = {c['name']: c['fields'] for c in json.loads((HERE / 'fixture_cases.json').read_text())
         if c['kind'] == 'ficdownloader'}
NOT_IN_FILE = ('langcode',)


class FicdownloaderTest(unittest.TestCase):

    def check(self, name):
        fields, sources = extract_fields(HERE / 'fixtures' / name)
        for key, expected in CASES[name].items():
            if key in NOT_IN_FILE:
                continue
            with self.subTest(key=key):
                value = fields.get(key)
                if key.startswith('date'):
                    value = value.strftime('%Y-%m-%d')
                self.assertEqual(value, expected)
        return fields, sources

    def test_coauthors_series_and_folded_summary(self):
        fields, sources = self.check('ficdownloader-coauthors-series.epub')
        # The OPF's single combined creator string does not replace the page's names.
        self.assertEqual(sources['author'], 'ficdownloader')
        self.assertNotIn('numChaptersTotal', fields)
        self.assertNotIn('Synthetic notes', fields['description'])
        self.assertNotIn('fold label', fields['description'])
        self.assertEqual(fields['siteabbrev'], 'ao3')

    def test_values_left_out_by_the_tool_stay_missing(self):
        fields, _ = self.check('ficdownloader-sparse-complete.epub')
        # No Fandom/Relationship/Warnings lines and an empty Summary: nothing invented.
        for key in ('fandoms', 'ships', 'warnings', 'description', 'series'):
            self.assertNotIn(key, fields)
        self.assertEqual(fields['numChaptersTotal'], 1)
        # Category is AO3's relationship category, never a fandom.
        self.assertEqual(fields['ao3categories'], ['M/M'])


if __name__ == '__main__':
    unittest.main()
