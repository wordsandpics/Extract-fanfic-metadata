"""FanFicFare title-page labels that can be the only record of a value."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'calibre_stub'))
sys.path.insert(0, str(HERE.parent))
from extract_epub_metadata.mapping import _map_titlepage, extract_fields  # noqa: E402


class FffTitlepageSeriesTest(unittest.TestCase):

    def test_series_and_author_url_from_title_page_only(self):
        fields, sources = extract_fields(HERE / 'fixtures' / 'fff-bold-series-only-titlepage.epub')
        self.assertEqual(fields['series'], 'Synthetic Outtakes Series [3]')
        self.assertEqual(fields['seriesUrl'], 'https://archiveofourown.org/series/98000652')
        self.assertEqual(fields['authorUrl'],
                         ['https://archiveofourown.org/users/TestWriter66/pseuds/TestWriter66'])
        for key in ('series', 'seriesUrl', 'authorUrl'):
            self.assertEqual(sources[key], 'fff_titlepage')

    def test_unrecognized_values_are_left_out(self):
        mapped = _map_titlepage({'label_entries': {
            'Series': 'Part 2 of Something',
            'Series URL': 'see profile',
            'Author URL': 'not a link',
        }})
        for key in ('series', 'seriesUrl', 'authorUrl'):
            self.assertNotIn(key, mapped)


if __name__ == '__main__':
    unittest.main()
