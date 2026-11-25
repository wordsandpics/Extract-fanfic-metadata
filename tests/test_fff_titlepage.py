"""FanFicFare title-page labels that can be the only record of a value."""
import io
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'calibre_stub'))
sys.path.insert(0, str(HERE.parent))
from extract_epub_metadata.calibre_fields import (  # noqa: E402
    compute_custom_column_values, compute_standard_fields)
from extract_epub_metadata.mapping import _derive_fields, _map_titlepage, extract_fields  # noqa: E402
from extract_epub_metadata.serialize import serialize_saved_metadata  # noqa: E402


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


class FffExtraEntriesTest(unittest.TestCase):
    """Title pages written with FanFicFare's optional AO3 entries switched on."""

    @staticmethod
    def read(name):
        return extract_fields(HERE / 'fixtures' / name)

    def test_chapters_categories_and_tags_are_recovered(self):
        fields, sources = self.read('fff-ao3-extra-entries-complete.epub')
        self.assertEqual(fields['numChapters'], 7)
        self.assertEqual(fields['numChaptersTotal'], 7)
        self.assertEqual(fields['chapterslashtotal'], '7/7')
        self.assertEqual(fields['ao3categories'], ['F/M', 'M/M'])
        self.assertEqual(fields['freeformtags'], ['TestTag68a', 'TestTag68b', 'TestTag68c'])
        for key in ('numChapters', 'numChaptersTotal', 'ao3categories', 'freeformtags'):
            self.assertEqual(sources[key], 'fff_titlepage')

    def test_live_counts_are_still_ignored(self):
        fields, _ = self.read('fff-ao3-extra-entries-complete.epub')
        for key in ('comments', 'kudos', 'hits', 'bookmarks'):
            self.assertNotIn(key, fields)

    def test_unfinished_story_keeps_count_without_a_total(self):
        fields, _ = self.read('fff-ao3-extra-entries-ongoing.epub')
        self.assertEqual(fields['numChapters'], 3)
        self.assertEqual(fields['chapterslashtotal'], '3/?')
        self.assertNotIn('numChaptersTotal', fields)
        self.assertEqual(fields['status'], 'In-Progress')
        self.assertEqual(fields['ao3categories'], ['Gen'])

    def test_calibre_tags_stay_free_of_duplicates(self):
        for name in ('fff-ao3-extra-entries-complete.epub', 'fff-ao3-extra-entries-ongoing.epub'):
            with self.subTest(name=name):
                tags = compute_standard_fields(self.read(name)[0])['tags']
                self.assertEqual(len(tags), len(set(tags)))
        tags = compute_standard_fields(self.read('fff-ao3-extra-entries-complete.epub')[0])['tags']
        self.assertEqual(tags.count('M/M'), 1)

    def test_linked_series_is_recovered(self):
        fields, sources = self.read('fff-ao3-extra-entries-complete.epub')
        self.assertEqual(fields['series'], 'Synthetic Linked Series [2]')
        self.assertEqual(fields['seriesUrl'], 'https://archiveofourown.org/series/98000703')
        self.assertEqual(sources['series'], 'fff_titlepage')
        self.assertNotIn('series', self.read('fff-ao3-extra-entries-ongoing.epub')[0])

    def test_series_link_address_is_used_only_with_an_accepted_series(self):
        link = {'Series': 'https://archiveofourown.org/series/98000703'}
        mapped = _map_titlepage({'label_entries': {'Series': 'Part 2 of Something'}, 'label_links': link})
        self.assertNotIn('series', mapped)
        self.assertNotIn('seriesUrl', mapped)
        mapped = _map_titlepage({'label_entries': {'Series': 'Name [2]'}, 'label_links': link})
        self.assertEqual(mapped['seriesUrl'], link['Series'])

    def test_explicit_series_url_line_wins_over_the_link(self):
        mapped = _map_titlepage({
            'label_entries': {'Series': 'Name [2]', 'Series URL': 'https://example.com/explicit'},
            'label_links': {'Series': 'https://example.com/from-link'}})
        self.assertEqual(mapped['seriesUrl'], 'https://example.com/explicit')


class FffLoggedInEntriesTest(unittest.TestCase):
    """Yes/no lines FanFicFare writes only when it was logged in to AO3."""

    KEYS = ('subscribed', 'bookmarked', 'markedforlater')
    COLUMNS = {
        '#sub': {'datatype': 'bool', 'is_multiple': False, 'display': {}},
        '#book': {'datatype': 'bool', 'is_multiple': False, 'display': {}},
        '#later': {'datatype': 'bool', 'is_multiple': False, 'display': {}},
        '#text': {'datatype': 'text', 'is_multiple': False, 'display': {}},
        '#num': {'datatype': 'int', 'is_multiple': False, 'display': {}},
    }
    MAPPING = {'#sub': 'subscribed', '#book': 'bookmarked', '#later': 'markedforlater'}

    @staticmethod
    def read(name):
        return extract_fields(HERE / 'fixtures' / name)

    def test_true_and_false_are_both_recovered(self):
        fields, sources = self.read('fff-ao3-logged-in-entries.epub')
        self.assertIs(fields['subscribed'], True)
        self.assertIs(fields['bookmarked'], False)
        self.assertIs(fields['markedforlater'], True)
        for key in self.KEYS:
            self.assertEqual(sources[key], 'fff_titlepage')

    def test_missing_lines_stay_unknown(self):
        for name in ('fff-ao3-extra-entries-complete.epub', 'fff-bold-packaged-date.epub'):
            fields, _ = self.read(name)
            for key in self.KEYS:
                self.assertNotIn(key, fields)

    def test_unrecognized_values_are_left_out(self):
        mapped = _map_titlepage({'label_entries': {
            'I Subscribed': 'maybe', 'I Bookmarked Story': '', 'I Marked for Later': ' TRUE '}})
        self.assertNotIn('subscribed', mapped)
        self.assertNotIn('bookmarked', mapped)
        self.assertIs(mapped['markedforlater'], True)

    def test_yes_no_columns_get_yes_and_no(self):
        fields, _ = self.read('fff-ao3-logged-in-entries.epub')
        self.assertEqual(compute_custom_column_values(fields, self.MAPPING, self.COLUMNS),
                         {'#sub': True, '#book': False, '#later': True})

    def test_missing_lines_write_nothing(self):
        fields, _ = self.read('fff-ao3-extra-entries-complete.epub')
        self.assertEqual(compute_custom_column_values(fields, self.MAPPING, self.COLUMNS), {})

    def test_only_yes_no_columns_are_written(self):
        fields, _ = self.read('fff-ao3-logged-in-entries.epub')
        self.assertEqual(compute_custom_column_values(
            fields, {'#text': 'subscribed', '#num': 'bookmarked'}, self.COLUMNS), {})

    def test_anthologies_have_none_of_them(self):
        fields, _ = self.read('anthology-mixed-status.epub')
        for key in self.KEYS:
            self.assertNotIn(key, fields)
        self.assertEqual(compute_custom_column_values(
            fields, self.MAPPING, self.COLUMNS, {'subscribed': True}), {})

    def test_calibre_tags_and_saved_metadata(self):
        fields, _ = self.read('fff-ao3-logged-in-entries.epub')
        self.assertNotIn('True', compute_standard_fields(fields).get('tags', []))
        saved = serialize_saved_metadata(fields)
        for key, word in (('subscribed', 'True'), ('bookmarked', 'False'), ('markedforlater', 'True')):
            self.assertIn("id='%s'>%s</div>" % (key, word), saved)


def with_title_page(name, old, new):
    """A copy of a fixture with one change to its title page, in memory."""
    buffer = io.BytesIO()
    with ZipFile(HERE / 'fixtures' / name) as source, ZipFile(buffer, 'w') as copy:
        for item in source.infolist():
            data = source.read(item.filename)
            if 'title_page' in item.filename:
                assert old.encode() in data
                data = data.replace(old.encode(), new.encode(), 1)
            copy.writestr(item, data)
    buffer.seek(0)
    return buffer


class SummaryTextTest(unittest.TestCase):
    """Labels an author typed inside the summary are not title-page facts."""

    NAME = 'fff-ao3-extra-entries-complete.epub'
    AUTHOR_TEXT = ('<p><b>Status:</b> on a break</p><p><b>Warnings:</b> read the notes<br />'
                   '<b>I Subscribed:</b> True<br /></p><p>Series: Not A Series [9]</p>')

    def check(self, opening, closing=''):
        expected, _ = extract_fields(HERE / 'fixtures' / self.NAME)
        stream = with_title_page(self.NAME, '<blockquote>', opening + self.AUTHOR_TEXT + closing)
        fields, _ = extract_fields(stream)
        for key in ('status', 'warnings', 'series'):
            self.assertEqual(fields[key], expected[key], key)
        self.assertNotIn('subscribed', fields)

    def test_bold_labels_in_a_quoted_summary_are_ignored(self):
        self.check('<blockquote>')

    def test_bold_labels_in_a_div_summary_are_ignored(self):
        # The other shape FanFicFare writes: <div class="userstuff">.
        self.check('<div class="userstuff">', '</div><blockquote>')


class MobileFanfictionTest(unittest.TestCase):

    def test_mobile_links_count_as_fanfiction_net(self):
        fields = {'storyUrl': 'https://m.fanfiction.net/s/98000001/1/Synthetic'}
        _derive_fields(fields)
        self.assertEqual((fields['site'], fields['siteabbrev'], fields['storyId']),
                         ('fanfiction.net', 'ffnet', '98000001'))
        self.assertEqual(fields['storyUrl'], 'https://m.fanfiction.net/s/98000001/1/Synthetic')


if __name__ == '__main__':
    unittest.main()
