"""AO3 HTML downloads, as Calibre stores them (ZIP book, or plain HTML)."""
import io
import json
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'calibre_stub'))
sys.path.insert(0, str(HERE.parent))
from extract_epub_metadata.extractors.html_zip import html_to_xhtml  # noqa: E402
from extract_epub_metadata.mapping import extract_html_fields  # noqa: E402

CASES = {c['name']: c['fields'] for c in json.loads((HERE / 'fixture_cases.json').read_text())
         if c['kind'].startswith('ao3_html')}
NOT_COMPARED = ('chapterslashtotal',)


class Ao3HtmlTest(unittest.TestCase):

    def check(self, name, is_zip=False, skip=()):
        fields, sources = extract_html_fields(HERE / 'fixtures' / name, is_zip=is_zip)
        for key, expected in CASES[name].items():
            if key in NOT_COMPARED or key in skip:
                continue
            with self.subTest(key=key):
                value = fields.get(key)
                if key.startswith('date'):
                    value = value.strftime('%Y-%m-%d')
                self.assertEqual(value, expected)
        self.assertEqual(set(sources.values()), {'ao3_html'})
        self.assertEqual((fields['formatname'], fields['formatext']), ('html', '.html'))
        return fields

    def test_current_download(self):
        fields = self.check('ao3-html-download.html')
        # The browser title ("Title - author - ...") is never used.
        self.assertNotIn('Browser', fields['title'])
        self.assertNotIn('Synthetic notes', fields['description'])
        self.assertNotIn('not the summary', fields['description'])
        self.assertEqual(fields['rating'], 'Teen And Up Audiences')

    def test_calibre_zip_copy(self):
        self.check('ao3-html-calibre-zip.zip', is_zip=True)

    def test_older_download_host(self):
        # download.archiveofourown.org links become ordinary AO3 links;
        # no Language line means no language is guessed.
        fields = self.check('ao3-html-older-download.html', skip=('language',))
        self.assertNotIn('language', fields)
        self.assertEqual(fields['storyUrl'], 'https://archiveofourown.org/works/98000691')

    def test_saved_web_page_is_not_read(self):
        self.assertEqual(extract_html_fields(HERE / 'fixtures' / 'ao3-html-saved-webpage.html',
                                             is_zip=False), ({}, {}))

    def test_unrelated_zip_and_html_are_not_read(self):
        archive = io.BytesIO()
        with ZipFile(archive, 'w') as z:
            z.writestr('page.html', '<p>Rating: Explicit</p><a href="https://archiveofourown.org/works/1">x</a>')
            z.writestr('image.txt', 'not html')
        archive.seek(0)
        self.assertEqual(extract_html_fields(archive), ({}, {}))
        self.assertEqual(extract_html_fields(io.BytesIO(b'not a zip')), ({}, {}))
        self.assertEqual(extract_html_fields(io.BytesIO(b'<html><p>Hi'), is_zip=False), ({}, {}))

    def test_sloppy_html_becomes_wellformed(self):
        out = html_to_xhtml(b'<p>One<br>two &amp; &nbsp;<p>Three<ul><li>a<li>b</ul></div><script>x<y</script>')
        self.assertIn(b'<br />', out)
        self.assertNotIn(b'x<y', out)
        self.assertEqual(out.count(b'<li>'), 2)


if __name__ == '__main__':
    unittest.main()
