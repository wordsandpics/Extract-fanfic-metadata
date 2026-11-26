"""Preview: values Calibre already holds are listed as up to date, not written."""
import datetime
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'calibre_stub'))
sys.path.insert(0, str(HERE.parent))
from extract_epub_metadata.calibre_fields import (  # noqa: E402
    split_unchanged_custom, split_unchanged_standard, value_matches,
)

UTC = datetime.timezone.utc


class FakeDB:
    def __init__(self, values):
        self.values = values

    def field_for(self, field, book_id, default_value=None):
        return self.values.get(field, default_value)


class ValueMatchesTest(unittest.TestCase):

    def test_same_values_match(self):
        self.assertTrue(value_matches('2/3 fics complete.\n1. A', '2/3 fics complete.\n1. A'))
        self.assertTrue(value_matches(26, 26))
        self.assertTrue(value_matches(('A', 'B'), ['A', 'B']))
        self.assertTrue(value_matches(False, False))
        when = datetime.datetime(2026, 11, 26, tzinfo=UTC)
        self.assertTrue(value_matches(when, when))

    def test_anything_uncertain_counts_as_a_change(self):
        self.assertFalse(value_matches('2/3 fics complete.', '3/3 fics complete.'))
        self.assertFalse(value_matches(('B', 'A'), ['A', 'B']))
        self.assertFalse(value_matches(None, 'Completed'))
        self.assertFalse(value_matches(0, False))
        self.assertFalse(value_matches(1, 1.0))
        naive = datetime.datetime(2026, 11, 26)
        self.assertTrue(value_matches(naive, naive))
        self.assertFalse(value_matches(naive.replace(tzinfo=UTC), naive))


class SplitTest(unittest.TestCase):

    def test_custom_columns(self):
        db = FakeDB({'#anthology_status': '2/3 fics complete.', '#words': 248000})
        changes, unchanged = split_unchanged_custom(
            db, 1, {'#anthology_status': '2/3 fics complete.', '#words': 248739})
        self.assertEqual(changes, {'#words': 248739})
        self.assertEqual(unchanged, {'#anthology_status': '2/3 fics complete.'})

    def test_standard_fields_outside_calibre(self):
        db = FakeDB({'title': 'Seated Rivalry Anthology', 'authors': ('devfiction',),
                     'languages': ('eng',), 'comments': '<p>Old</p>'})
        changes, unchanged = split_unchanged_standard(
            db, 1, {'title': 'Seated Rivalry Anthology', 'authors': ['devfiction'],
                    'language': 'en', 'comments': '<p>New</p>'})
        self.assertEqual(set(unchanged), {'title', 'authors'})
        # Comments and language need Calibre to compare; without it they are written.
        self.assertEqual(set(changes), {'language', 'comments'})

    def test_series_name_and_number(self):
        db = FakeDB({'series': 'Seated Rivalry', 'series_index': 2.0})
        _, unchanged = split_unchanged_standard(db, 1, {'series': 'Seated Rivalry [2]'})
        self.assertEqual(set(unchanged), {'series'})
        changes, _ = split_unchanged_standard(db, 1, {'series': 'Seated Rivalry [3]'})
        self.assertEqual(set(changes), {'series'})


if __name__ == '__main__':
    unittest.main()
