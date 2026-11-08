"""Synthetic fixture regressions; run with unittest discovery."""
import io
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'calibre_stub'))
sys.path.insert(0, str(HERE.parent))
from extract_epub_metadata.calibre_fields import compute_custom_column_values, compute_standard_fields
from extract_epub_metadata.collections import extract_collection
from extract_epub_metadata.extractors._numbers import parse_count
from extract_epub_metadata.mapping import extract_fields
from extract_epub_metadata.serialize import serialize_saved_metadata
FIXTURES = HERE / 'fixtures'
FRESH = FIXTURES
MULTI = FIXTURES / 'anthology-multiple-authors.epub'

class CollectionExtractionTest(unittest.TestCase):

    def test_multi_author_records_and_complete_totals(self):
        fields, sources = extract_fields(MULTI)
        self.assertEqual(fields['author'], ['TestWriter14', 'TestWriter15'])
        self.assertEqual(fields['collectionStoryCount'], 5)
        self.assertEqual(fields['collectionCompletedCount'], 5)
        self.assertEqual(fields['collectionUnknownCount'], 0)
        self.assertEqual(fields['numWords'], 93149)
        self.assertEqual(fields['collectionChapterCount'], 66)
        records = fields['collectionRecords']
        self.assertEqual([r['author'] for r in records], [['TestWriter14']] * 2 + [['TestWriter14', 'TestWriter15']] * 3)
        self.assertTrue(all((r.get('description') for r in records)))
        self.assertEqual(records[0]['rating'], 'Teen And Up Audiences')
        self.assertEqual(records[-1]['rating'], 'Explicit')
        self.assertEqual(sources['numWords'], 'collection_stories')
        for key in ('rating', 'warnings', 'storyUrl', 'numChapters', 'status', 'datePublished'):
            self.assertNotIn(key, fields)
        with self.assertRaises(ValueError):
            serialize_saved_metadata(fields)

    def test_mixed_completion_does_not_become_first_story_status(self):
        fields, _ = extract_fields(FIXTURES / 'anthology-mixed-status.epub')
        self.assertEqual(fields['collectionStoryCount'], 7)
        self.assertEqual(fields['collectionCompletedCount'], 6)
        self.assertEqual(fields['collectionRecords'][-1]['status'], 'In-Progress')
        self.assertNotIn('datePublished', fields['collectionRecords'][-1])
        self.assertNotIn('status', fields)

    def test_series_page_facts_without_fabricated_story_records(self):
        fields, sources = extract_fields(FRESH / 'ao3-series-collection.epub')
        self.assertEqual(fields['collectionType'], 'series collection')
        self.assertEqual(fields['collectionStoryCount'], 2)
        self.assertEqual(fields['numWords'], 11822)
        self.assertEqual(fields['collectionStatus'], 'In-Progress')
        self.assertEqual(fields['collectionDateBegun'].isoformat(), '2018-11-24T00:00:00')
        self.assertEqual(fields['collectionDateUpdated'].isoformat(), '2019-05-31T00:00:00')
        self.assertEqual(sources['collectionStatus'], 'collection_series_page')
        for key in ('collectionRecords', 'collectionCompletedCount', 'collectionChapterCount', 'storyUrl'):
            self.assertNotIn(key, fields)

    def test_work_with_series_link_stays_single_story(self):
        fields, _ = extract_fields(FRESH / 'ao3-information-thin-space.epub')
        self.assertNotIn('collectionType', fields)
        self.assertEqual(fields['storyUrl'], 'https://archiveofourown.org/works/98000408')
        self.assertIn('series', fields)

    def test_missing_story_count_prevents_partial_total(self):
        buf = io.BytesIO()
        with ZipFile(MULTI) as source, ZipFile(buf, 'w') as target:
            for name in source.namelist():
                data = source.read(name)
                if name == '1/OEBPS/title_page.xhtml':
                    data = data.replace(b'572', b'unknown')
                target.writestr(name, data)
        buf.seek(0)
        fields, _ = extract_fields(buf)
        self.assertNotIn('numWords', fields)
        self.assertEqual(fields['collectionChapterCount'], 66)

    def test_outer_tags_remain_tags_without_changing_status(self):
        fields, _ = extract_fields(FRESH / 'anthology-outer-status-tag.epub')
        computed = compute_standard_fields(fields)
        self.assertEqual(computed['tags'], sorted(set(fields['collectionTags'])))
        self.assertEqual(fields['collectionCompletedCount'], 2)
        self.assertIn('In-Progress', computed['tags'])
        self.assertNotIn('pubdate', computed)
        self.assertNotIn('series', computed)

    def test_custom_columns_use_collection_keys_and_accept_zero(self):
        fields, _ = extract_fields(MULTI)
        columns = {k: {'datatype': 'int'} for k in ('#words', '#count', '#unknown')}
        columns['#rating'] = {'datatype': 'text'}
        values = compute_custom_column_values(fields, {'#words': 'numWords', '#count': 'collectionStoryCount', '#unknown': 'collectionUnknownCount', '#rating': 'rating'}, columns)
        self.assertEqual(values, {'#words': 93149, '#count': 5, '#unknown': 0})

    def test_series_marker_uses_primary_url_not_an_incidental_link(self):
        with ZipFile(FRESH / 'ao3-series-collection.epub') as zf:
            result = extract_collection(zf, {'identifiers': {'url': 'https://archiveofourown.org/works/123'}, 'dc_source': 'https://archiveofourown.org/series/98000411'})
            self.assertIsNone(result)
            fields, _ = extract_collection(zf, {'identifiers': {'uri': 'https://web.archive.org/web/20200101000000/https://archiveofourown.org/series/98000411'}})
            self.assertEqual(fields['collectionUrl'], 'https://archiveofourown.org/series/98000411')
            self.assertIn('waybackUrl', fields)

class FreshNumericTest(unittest.TestCase):

    def test_webtoepub_thin_space_words(self):
        fields, _ = extract_fields(FRESH / 'ao3-information-thin-space.epub')
        self.assertEqual(fields['numWords'], 111536)
        self.assertEqual(fields['numChapters'], 24)

    def test_save_as_ebook_space_words(self):
        path = next(FRESH.glob('ao3-browser-space-counts.epub'))
        fields, _ = extract_fields(path)
        self.assertEqual(fields['numWords'], 3334)
        self.assertEqual(fields['numChapters'], 1)

    def test_counts_reject_ambiguous_or_partial_values(self):
        for text in ('12/24', '12/?', 'about 100', '12 34', '1,23', '-5', '1.5', True):
            self.assertIsNone(parse_count(text), text)
        for text in ('1,234', '1 234', '1\u2009234', '1\xa0234', '1\u202f234'):
            self.assertEqual(parse_count(text), 1234, text)
        self.assertEqual(parse_count(0), 0)

class AnthologyPreviewFactsTest(unittest.TestCase):
    """Step 2 of the anthology version: facts gathered for the preview only."""

    def test_story_lists_from_title_page(self):
        from extract_epub_metadata.anthology import _add_story_lists
        ao3 = {'storyUrl': 'https://archiveofourown.org/works/1'}
        _add_story_lists({'category': 'Fandom A, Fandom B', 'characters': 'X, Y',
                          'relationships': 'X/Y', 'genre': 'M/M, Fluff'}, ao3)
        self.assertEqual(ao3['fandoms'], ['Fandom A', 'Fandom B'])
        self.assertEqual(ao3['characters'], ['X', 'Y'])
        self.assertEqual(ao3['ships'], ['X/Y'])
        self.assertNotIn('freeformtags', ao3)
        other = {'storyUrl': 'https://forums.spacebattles.com/threads/1/'}
        _add_story_lists({'category': 'AU'}, other)
        self.assertNotIn('fandoms', other)

    def test_combined_lists_and_date_range(self):
        import datetime
        from extract_epub_metadata.collections import _combined_story_fields
        d = datetime.datetime
        records = [
            {'fandoms': ['A'], 'characters': ['X', 'Y'], 'datePublished': d(2012, 5, 1), 'dateUpdated': d(2012, 6, 1)},
            {'fandoms': ['B', 'A'], 'characters': ['Y', 'Z'], 'datePublished': d(2011, 1, 1), 'dateUpdated': d(2015, 1, 1)},
            {'ships': ['X/Z']},
        ]
        combined = _combined_story_fields(records)
        self.assertEqual(combined['collectionFandoms'], ['A', 'B'])
        self.assertEqual(combined['collectionCharacters'], ['X', 'Y', 'Z'])
        self.assertEqual(combined['collectionShips'], ['X/Z'])
        self.assertEqual(combined['collectionEarliestPublished'], d(2011, 1, 1))
        self.assertEqual(combined['collectionLatestUpdated'], d(2015, 1, 1))
        self.assertEqual(_combined_story_fields([{}]), {})

    def test_series_status_is_the_single_outer_status_tag(self):
        from extract_epub_metadata.collections import _series_status
        self.assertEqual(_series_status({'subjects': ['Fluff', 'Completed']}), 'Completed')
        self.assertIsNone(_series_status({'subjects': ['Fluff']}))
        self.assertIsNone(_series_status({'subjects': ['Completed', 'In-Progress']}))
        fields, _ = extract_fields(FRESH / 'anthology-complete.epub')
        self.assertEqual(fields['collectionSeriesStatus'], 'Completed')

    def test_preview_facts_are_not_written_anywhere_yet(self):
        from extract_epub_metadata.calibre_fields import ALL_METADATA_KEYS
        fields, _ = extract_fields(FRESH / 'anthology-mixed-status.epub')
        new_keys = {'collectionSeriesStatus', 'collectionEarliestPublished', 'collectionLatestUpdated',
                    'collectionFandoms', 'collectionCharacters', 'collectionShips'}
        self.assertTrue(new_keys & set(fields))
        self.assertFalse(new_keys & set(ALL_METADATA_KEYS))
        computed = compute_standard_fields(fields)
        self.assertNotIn('pubdate', computed)



class AlsoForAnthologiesTest(unittest.TestCase):
    """Step 3: ticked column-mapping rows take the anthology-wide value."""

    @classmethod
    def setUpClass(cls):
        import datetime
        cls.d = datetime.datetime
        cls.fields = {
            'collectionType': 'epubmerge anthology', 'numWords': 500,
            'collectionSeriesStatus': 'In-Progress', 'collectionChapterCount': 12,
            'collectionEarliestPublished': cls.d(2011, 1, 1), 'collectionLatestUpdated': cls.d(2015, 1, 1),
            'collectionFandoms': ['A', 'B'], 'collectionCharacters': ['X'],
            'collectionRatings': ['Mature', 'Explicit'], 'collectionHighestRating': 'Explicit',
        }
        cls.columns = {
            '#status': {'datatype': 'text'}, '#done': {'datatype': 'bool'},
            '#pub': {'datatype': 'datetime'}, '#upd': {'datatype': 'datetime'},
            '#ch': {'datatype': 'int'}, '#fandom': {'datatype': 'text', 'is_multiple': True},
            '#chars': {'datatype': 'text', 'is_multiple': True}, '#rating': {'datatype': 'text'},
            '#words': {'datatype': 'int'},
        }
        cls.mapping = {'#status': 'status', '#done': 'status-C (Completed = checked)',
                       '#pub': 'datePublished', '#upd': 'dateUpdated', '#ch': 'numChapters',
                       '#fandom': 'fandoms', '#chars': 'characters', '#rating': 'rating',
                       '#words': 'numWords'}

    def test_unticked_rows_stay_empty_for_anthologies(self):
        values = compute_custom_column_values(self.fields, self.mapping, self.columns)
        self.assertEqual(values, {'#words': 500})

    def test_ticked_rows_take_anthology_values(self):
        choices = {k: True for k in self.mapping.values()}
        choices['rating'] = 'highest'
        values = compute_custom_column_values(self.fields, self.mapping, self.columns, choices)
        self.assertEqual(values, {
            '#status': 'In-Progress', '#done': False, '#pub': self.d(2011, 1, 1),
            '#upd': self.d(2015, 1, 1), '#ch': 12, '#fandom': ['A', 'B'], '#chars': ['X'],
            '#rating': 'Explicit', '#words': 500})

    def test_rating_all_and_enumeration_columns(self):
        values = compute_custom_column_values(self.fields, {'#rating': 'rating'}, self.columns,
                                              {'rating': 'all'})
        self.assertEqual(values, {'#rating': 'Mature, Explicit'})
        enum = {'#rating': {'datatype': 'enumeration',
                            'display': {'enum_values': ['Mature', 'Explicit']}}}
        values = compute_custom_column_values(self.fields, {'#rating': 'rating'}, enum, {'rating': 'all'})
        self.assertEqual(values, {})
        values = compute_custom_column_values(self.fields, {'#rating': 'rating'}, enum, {'rating': 'highest'})
        self.assertEqual(values, {'#rating': 'Explicit'})

    def test_status_stays_empty_without_series_status(self):
        fields = dict(self.fields)
        del fields['collectionSeriesStatus']
        values = compute_custom_column_values(
            fields, {'#status': 'status', '#done': 'status-C (Completed = checked)'}, self.columns,
            {'status': True, 'status-C (Completed = checked)': True})
        self.assertEqual(values, {})

    def test_single_stories_ignore_anthology_ticks(self):
        story = {'status': 'Completed', 'numChapters': 3, 'collectionChapterCount': 99}
        values = compute_custom_column_values(story, {'#status': 'status', '#ch': 'numChapters'},
                                              self.columns, {'status': True, 'numChapters': True})
        self.assertEqual(values, {'#status': 'Completed', '#ch': 3})

    def test_published_date_is_opt_in(self):
        self.assertNotIn('pubdate', compute_standard_fields(self.fields))
        self.assertEqual(compute_standard_fields(self.fields, anthology_pubdate=True)['pubdate'],
                         self.d(2011, 1, 1))

    def test_highest_rating_rules(self):
        from extract_epub_metadata.collections import _combined_story_fields
        ao3 = 'https://archiveofourown.org/works/%d'
        ffnet = 'https://www.fanfiction.net/s/%d/'
        def highest(*stories):
            records = [{'storyUrl': url % i, 'rating': rating} for i, (url, rating) in enumerate(stories)]
            return _combined_story_fields(records).get('collectionHighestRating')
        self.assertEqual(highest((ao3, 'Teen And Up Audiences'), (ao3, 'Mature')), 'Mature')
        self.assertIsNone(highest((ao3, 'Mature'), (ao3, 'Not Rated')))
        self.assertIsNone(highest((ao3, 'Mature'), (ao3, '')))
        self.assertIsNone(highest((ao3, 'Mature'), (ffnet, 'M')))
        self.assertEqual(highest((ffnet, 'Fiction K+'), (ffnet, 'Fiction T')), 'T')


if __name__ == '__main__':
    unittest.main()
