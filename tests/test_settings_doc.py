"""SETTINGS.md and the mapping dialog describe the same fields."""
import re
import sys
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE/'calibre_stub'),str(HERE.parent)]
from extract_epub_metadata.calibre_fields import ALL_METADATA_KEYS, field_help, field_label

DOC=(HERE.parent/'SETTINGS.md').read_text(encoding='utf-8')


class SettingsDocTests(unittest.TestCase):
    def test_every_field_has_hover_help(self):
        self.assertEqual([k for k in ALL_METADATA_KEYS if not field_help(k)],[])

    def test_every_field_is_documented_once(self):
        rows=re.findall(r'^\| ([^|]+?) \| [^|]+ \| [^|]+ \|$',DOC,re.M)
        labels=[field_label(k) for k in ALL_METADATA_KEYS]
        self.assertEqual(sorted(r for r in rows if r in labels),sorted(labels))


    def test_every_anthology_choice_has_help_and_is_documented(self):
        from extract_epub_metadata.calibre_fields import ANTHOLOGY_HELP, ANTHOLOGY_PAIRS
        self.assertEqual(sorted(ANTHOLOGY_HELP), sorted(ANTHOLOGY_PAIRS))
        section = DOC.split('\n## Anthologies\n', 1)[1].split('\n## ', 1)[0]
        table = [line for line in section.splitlines() if line.startswith('| ')]
        for key in ANTHOLOGY_PAIRS:
            self.assertTrue(any(field_label(key) in line.split(' | ')[0] for line in table), key)


if __name__=='__main__':
    unittest.main()
