"""AO3 stories saved through AO3 Saver (a mirror that keeps AO3's own preface)."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'calibre_stub'))
sys.path.insert(0, str(HERE.parent))
from extract_epub_metadata.mapping import extract_fields  # noqa: E402

CASE = next(c['fields'] for c in json.loads((HERE / 'fixture_cases.json').read_text())
            if c['name'] == 'ao3saver-coauthors.epub')


class Ao3SaverTest(unittest.TestCase):

    def setUp(self):
        self.fields, self.sources = extract_fields(HERE / 'fixtures' / 'ao3saver-coauthors.epub')

    def test_every_stated_value_is_recovered(self):
        for key, expected in CASE.items():
            with self.subTest(key=key):
                value = self.fields.get(key)
                if key.startswith('date'):
                    value = value.strftime('%Y-%m-%d')
                self.assertEqual(value, expected)

    def test_real_ao3_link_replaces_the_mirror_address(self):
        self.assertEqual(self.fields['storyUrl'], 'https://archiveofourown.org/works/98000641')
        self.assertEqual(self.fields['site'], 'archiveofourown.org')
        self.assertEqual(self.fields['storyId'], '98000641')

    def test_unmarked_byline_is_used_and_credits_are_not(self):
        self.assertEqual(self.sources['author'], 'ao3_frontmatter')
        self.assertNotIn('TestOther', self.fields['author'])
        self.assertEqual(self.fields['authorId'], ['TestWriter64', 'TestPseud65'])
        self.assertNotIn('Synthetic notes', self.fields['description'])
        # The OPF title carries the mirror's "Title - Author - Fandom" form.
        self.assertEqual(self.fields['title'], 'Synthetic AO3 Saver Coauthors')


if __name__ == '__main__':
    unittest.main()
