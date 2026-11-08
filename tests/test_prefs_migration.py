"""The 1.3.0 carry-over of the former anthology report action's settings."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'calibre_stub'))
sys.path.insert(0, str(HERE.parent))
from extract_epub_metadata.calibre_fields import (  # noqa: E402
    compatible_columns_for_key, compute_custom_column_values, field_label,
)
from extract_epub_metadata.mapping import extract_fields  # noqa: E402
from extract_epub_metadata.prefs_migration import migrate_anthology_report  # noqa: E402

OLD = {'destColumn': '#saved', 'mode3Enabled': True, 'columnMapping': {'#words': 'numWords'},
       'anthologyDestColumn': '#anthology_status', 'anthologyOverwrite': True,
       'anthologyPreview': True, 'anthologyShowConfirmation': True}


class AnthologyReportMigrationTest(unittest.TestCase):

    def test_report_column_joins_the_mapping_once(self):
        new, changed = migrate_anthology_report(dict(OLD))
        self.assertTrue(changed)
        self.assertEqual(new['columnMapping'],
                         {'#words': 'numWords', '#anthology_status': 'collectionStoryReport'})
        for key in ('anthologyDestColumn', 'anthologyOverwrite', 'anthologyPreview',
                    'anthologyShowConfirmation'):
            self.assertNotIn(key, new)
        self.assertTrue(new['mode3Enabled'])
        # A later unmapping by the user is not undone.
        new['columnMapping'].pop('#anthology_status')
        again, changed = migrate_anthology_report(new)
        self.assertFalse(changed)
        self.assertEqual(again['columnMapping'], {'#words': 'numWords'})

    def test_custom_columns_switched_on_only_when_report_is_the_only_mapping(self):
        only = dict(OLD, mode3Enabled=False, columnMapping={})
        new, _ = migrate_anthology_report(only)
        self.assertTrue(new['mode3Enabled'])
        others = dict(OLD, mode3Enabled=False)
        new, _ = migrate_anthology_report(others)
        self.assertFalse(new['mode3Enabled'])
        self.assertEqual(new['columnMapping']['#anthology_status'], 'collectionStoryReport')

    def test_conflicts_leave_the_mapping_alone(self):
        taken = dict(OLD, columnMapping={'#anthology_status': 'description'})
        new, _ = migrate_anthology_report(taken)
        self.assertEqual(new['columnMapping'], {'#anthology_status': 'description'})
        reserved = dict(OLD, anthologyDestColumn='#saved')
        new, _ = migrate_anthology_report(reserved)
        self.assertEqual(new['columnMapping'], {'#words': 'numWords'})
        new, _ = migrate_anthology_report(dict(OLD, anthologyDestColumn=''))
        self.assertEqual(new['columnMapping'], {'#words': 'numWords'})


class AnthologyStoryReportFieldTest(unittest.TestCase):

    def test_report_field_writes_the_same_text_to_long_text_columns(self):
        from zipfile import ZipFile
        from extract_epub_metadata.anthology import extract_fic_records, format_summary
        path = HERE / 'fixtures' / 'anthology-mixed-status.epub'
        fields, _ = extract_fields(path)
        with ZipFile(path) as zf:
            self.assertEqual(fields['collectionStoryReport'], format_summary(extract_fic_records(zf)))
        columns = {'#anthology_status': {'datatype': 'comments'}, '#short': {'datatype': 'text'}}
        self.assertEqual(compatible_columns_for_key('collectionStoryReport', columns), ['#anthology_status'])
        values = compute_custom_column_values(
            fields, {'#anthology_status': 'collectionStoryReport'}, columns)
        self.assertTrue(values['#anthology_status'].startswith('6/7 fics complete.\n'))
        self.assertEqual(field_label('collectionStoryReport'), 'Anthology Story Report')

    def test_single_stories_have_no_report(self):
        fields, _ = extract_fields(HERE / 'fixtures' / 'ao3-information-ongoing.epub')
        self.assertNotIn('collectionStoryReport', fields)


if __name__ == '__main__':
    unittest.main()
