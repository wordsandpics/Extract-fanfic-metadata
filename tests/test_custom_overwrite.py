"""Custom columns: unticked "Overwrite" rows only fill empty columns."""
import datetime
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'calibre_stub'))
sys.path.insert(0, str(HERE.parent))
from extract_epub_metadata.calibre_fields import (  # noqa: E402
    apply_custom_column_mapping, compute_custom_column_values, custom_column_is_populated,
    plan_custom_columns,
)


class FakeDB:
    def __init__(self, values):
        self.values = dict(values)

    def field_for(self, field, book_id, default_value=None):
        return self.values.get(field, default_value)

    def set_field(self, field, mapping):
        changed = set()
        for book_id, value in mapping.items():
            if self.values.get(field) != value:
                self.values[field] = value
                changed.add(book_id)
        return changed


COLUMNS = {
    '#status': {'datatype': 'text'}, '#done': {'datatype': 'bool'},
    '#ch': {'datatype': 'int'}, '#words': {'datatype': 'int'},
    '#fandom': {'datatype': 'text', 'is_multiple': True},
    '#upd': {'datatype': 'datetime'}, '#stars': {'datatype': 'rating'},
}
MAPPING = {'#status': 'status', '#ch': 'numChapters', '#words': 'numWords',
           '#fandom': 'fandoms', '#upd': 'dateUpdated'}
STORY = {'status': 'Completed', 'numChapters': 3, 'numWords': 9000,
         'fandoms': ['Synthetic Fandom'], 'dateUpdated': datetime.datetime(2020, 5, 1)}


class PopulatedTest(unittest.TestCase):

    def test_what_counts_as_filled(self):
        self.assertTrue(custom_column_is_populated(COLUMNS['#done'], False))
        self.assertTrue(custom_column_is_populated(COLUMNS['#ch'], 0))
        self.assertFalse(custom_column_is_populated(COLUMNS['#ch'], None))
        self.assertFalse(custom_column_is_populated(COLUMNS['#stars'], 0))
        self.assertFalse(custom_column_is_populated(COLUMNS['#status'], ''))
        self.assertFalse(custom_column_is_populated(COLUMNS['#fandom'], ()))
        self.assertFalse(custom_column_is_populated(COLUMNS['#upd'], None))
        self.assertTrue(custom_column_is_populated(COLUMNS['#fandom'], ('Hand-picked',)))


class PlanTest(unittest.TestCase):

    def setUp(self):
        self.computed = compute_custom_column_values(STORY, MAPPING, COLUMNS)
        self.db = FakeDB({'#status': 'In-Progress', '#fandom': ('Hand-picked',), '#ch': 0})

    def test_unticked_columns_fill_blanks_only(self):
        pending, skipped, _ = plan_custom_columns(self.db, 1, self.computed, MAPPING, COLUMNS, {})
        self.assertEqual(set(pending), {'#words', '#upd'})
        self.assertEqual(set(skipped), {'#status', '#fandom', '#ch'})
        self.assertEqual(skipped['#status'], 'Completed')

    def test_ticked_status_updates_while_others_fill_blanks(self):
        pending, skipped, _ = plan_custom_columns(self.db, 1, self.computed, MAPPING, COLUMNS,
                                               {'status': True})
        self.assertEqual(set(pending), {'#status', '#words', '#upd'})
        self.assertEqual(set(skipped), {'#fandom', '#ch'})

    def test_all_ticked_matches_previous_behaviour(self):
        ticks = {key: True for key in MAPPING.values()}
        pending, skipped, _ = plan_custom_columns(self.db, 1, self.computed, MAPPING, COLUMNS, ticks)
        self.assertEqual(pending, self.computed)
        self.assertEqual(skipped, {})

    def test_anthology_status_ticked_keeps_other_columns(self):
        anthology = {'collectionType': 'epubmerge anthology', 'numWords': 500,
                     'collectionSeriesStatus': 'Completed', 'collectionFandoms': ['A', 'B']}
        computed = compute_custom_column_values(anthology, MAPPING, COLUMNS,
                                                {'status': True, 'fandoms': True})
        db = FakeDB({'#status': 'In-Progress', '#fandom': ('FanFicFare wrangled',), '#words': 480})
        pending, skipped, _ = plan_custom_columns(db, 1, computed, MAPPING, COLUMNS, {'status': True})
        self.assertEqual(pending, {'#status': 'Completed'})
        self.assertEqual(set(skipped), {'#fandom', '#words'})


class WriteTest(unittest.TestCase):

    def test_write_rechecks_columns_filled_after_preview(self):
        db = FakeDB({})
        computed = compute_custom_column_values(STORY, MAPPING, COLUMNS)
        pending, _, fill_only = plan_custom_columns(db, 1, computed, MAPPING, COLUMNS, {'status': True})
        self.assertNotIn('#status', fill_only)
        db.values['#words'] = 1234
        db.values['#status'] = 'In-Progress'
        written = apply_custom_column_mapping(db, 1, pending, None, fill_only, COLUMNS)
        self.assertEqual(db.values['#words'], 1234)
        self.assertEqual(db.values['#status'], 'Completed')
        self.assertNotIn('#words', written)
        self.assertIn('#status', written)

    def test_without_column_details_everything_is_written(self):
        db = FakeDB({'#status': 'In-Progress'})
        apply_custom_column_mapping(db, 1, {'#status': 'Completed'})
        self.assertEqual(db.values['#status'], 'Completed')


if __name__ == '__main__':
    unittest.main()
