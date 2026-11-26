from calibre.utils.config import JSONConfig
from qt.core import (
    QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget,
)

from calibre_plugins.extract_epub_metadata.dialogs import ColumnMappingDialog
from calibre_plugins.extract_epub_metadata.prefs_migration import migrate_anthology_report

# Extra vertical breathing room between the three mode group boxes, so
# they read as clearly separate choices rather than one dense block.
GROUP_SPACING = 14


def _subtext_label(text, parent):
    label = QLabel(text, parent)
    label.setWordWrap(True)
    font = label.font()
    font.setItalic(True)
    label.setFont(font)
    return label


STORE_NAME = 'Options'

KEY_MODE1_ENABLED = 'mode1Enabled'
KEY_DEST_COLUMN = 'destColumn'
KEY_OVERWRITE = 'overwrite'

KEY_MODE2_ENABLED = 'mode2Enabled'
KEY_MODE2_OVERWRITE = 'mode2Overwrite'

KEY_MODE3_ENABLED = 'mode3Enabled'
KEY_COLUMN_MAPPING = 'columnMapping'
# {story field key: True | 'highest' | 'all'} for column-mapping rows ticked
# "Anthologies too" (calibre_fields.ANTHOLOGY_PAIRS).
KEY_ANTHOLOGY_FIELDS = 'anthologyFields'
# {story field key: True} for column-mapping rows ticked "Overwrite"; other
# mapped columns are only filled when empty.
KEY_CUSTOM_OVERWRITE = 'customOverwrite'
# Standard metadata: set Published to the earliest story's date for anthologies.
KEY_ANTHOLOGY_PUBDATE = 'anthologyPubdate'

KEY_ADD_IDENTIFIER = 'addMissingIdentifier'
KEY_PREVIEW = 'preview'
KEY_SHOW_CONFIRMATION = 'showConfirmation'

# The former "Extract story status from anthology" action's settings are
# carried into the column mapping once (prefs_migration.py).

DEFAULT_STORE_VALUES = {
    # A new install (1.4.2 on) starts with standard metadata on and Saved
    # Metadata off: Saved Metadata needs a column chosen first, so it could not
    # work out of the box. Preview stays on, so nothing is written unseen.
    # Existing settings keep their write options; see EARLIER_MODE_DEFAULTS.
    KEY_MODE1_ENABLED: False,
    KEY_DEST_COLUMN: '',
    KEY_OVERWRITE: False,

    KEY_MODE2_ENABLED: True,
    KEY_MODE2_OVERWRITE: False,
    KEY_ANTHOLOGY_PUBDATE: False,

    KEY_MODE3_ENABLED: False,
    KEY_COLUMN_MAPPING: {},
    KEY_ANTHOLOGY_FIELDS: {},
    KEY_CUSTOM_OVERWRITE: {},

    KEY_ADD_IDENTIFIER: True,
    KEY_PREVIEW: True,
    KEY_SHOW_CONFIRMATION: True,
}

# The write options' defaults before 1.4.2. Settings saved by an earlier version
# that lack one of these keys keep the old value, so an update never starts
# writing to a library on its own.
EARLIER_MODE_DEFAULTS = {KEY_MODE1_ENABLED: True, KEY_MODE2_ENABLED: False, KEY_MODE3_ENABLED: False}

# Always prefix with 'plugins/' so this doesn't collide with a core calibre
# config file.
plugin_prefs = JSONConfig('plugins/Extract Epub Metadata')
plugin_prefs.defaults[STORE_NAME] = DEFAULT_STORE_VALUES


def get_prefs():
    """
    Returns the stored 'Options' dict, backfilled with any keys added to
    DEFAULT_STORE_VALUES since the store was last saved. JSONConfig only
    supplies its `.defaults` when the top-level key ('Options') is missing
    entirely -- it does NOT deep-merge new sub-keys into an already-stored
    dict, so a plain `plugin_prefs[STORE_NAME]` lookup raises KeyError for
    any key added after a user's settings were first saved (confirmed via
    calibre-debug against a real settings file predating mode 2's keys).
    Always read prefs through this function, never `plugin_prefs[STORE_NAME]`
    directly.
    """
    existing = STORE_NAME in plugin_prefs
    stored, changed = migrate_anthology_report(dict(plugin_prefs[STORE_NAME]))
    if changed:
        plugin_prefs[STORE_NAME] = stored
    prefs = dict(DEFAULT_STORE_VALUES)
    if existing:
        prefs.update(EARLIER_MODE_DEFAULTS)
    prefs.update(stored)
    return prefs


def _add_other_library_column(combo, column_key, custom_columns):
    """Settings are shared by every library: keep a Saved Metadata column this
    library doesn't have, so saving here doesn't clear it for the others."""
    if column_key and column_key not in custom_columns:
        combo.addItem('%s (not in this library)' % column_key, column_key)


class ConfigWidget(QWidget):
    """The Extract Metadata settings: the three write modes and shared
    options. (Until 1.3.0 a second tab held the separate anthology report
    action's settings; that report is now a column-mapping field.)"""

    def __init__(self, plugin_action):
        QWidget.__init__(self)
        self.plugin_action = plugin_action
        self.gui = plugin_action.gui

        prefs = get_prefs()
        custom_columns = self.gui.library_view.model().custom_columns
        self.custom_columns = custom_columns

        outer = QVBoxLayout(self)
        self.setLayout(outer)

        outer.addWidget(self._build_extraction_tab(prefs, custom_columns))
        self._refresh_saved_columns()

    def _refresh_saved_columns(self):
        # Prevent new conflicts even in Calibre versions whose configuration
        # dialog does not support validate_before_accept.
        current = self.dest_column.currentData()
        self.dest_column.blockSignals(True)
        self.dest_column.clear()
        self.dest_column.addItem('', '')
        for key, column in sorted(self.custom_columns.items()):
            if column['datatype'] == 'comments' and key not in self.column_mapping:
                self.dest_column.addItem(column['name'], key)
        _add_other_library_column(self.dest_column, current, self.custom_columns)
        idx = self.dest_column.findData(current)
        self.dest_column.setCurrentIndex(max(0, idx))
        self.dest_column.blockSignals(False)
        self.saved_column_note.setText(
            'The previous Saved Metadata column is already mapped. Choose another column '
            'or remove that custom mapping.' if current and idx < 0 else '')

    def validate(self):
        reserved = self.dest_column.currentData()
        if reserved and reserved in self.column_mapping:
            from calibre.gui2 import error_dialog
            error_dialog(self, 'Conflicting column settings',
                         'The Saved Metadata column is also a custom mapping destination. '
                         'Open Configure column mapping and choose a different destination.', show=True)
            return False
        return True

    validate_before_accept = True

    def _build_extraction_tab(self, prefs, custom_columns):
        tab = QWidget(self)
        layout = QVBoxLayout(tab)

        layout.addWidget(self._build_mode1_group(prefs, custom_columns))
        layout.addSpacing(GROUP_SPACING)
        layout.addWidget(self._build_mode2_group(prefs))
        layout.addSpacing(GROUP_SPACING)
        layout.addWidget(self._build_mode3_group(prefs, custom_columns))
        layout.addSpacing(GROUP_SPACING)

        self.add_identifier = QCheckBox(
            'Add missing story-URL identifier', tab)
        self.add_identifier.setToolTip(
            "FanFicFare needs a recognized story URL (Calibre's 'url' or "
            "'uri' identifier) to pick the right site adapter when it reads "
            "back the Saved Metadata column. If checked, a recovered story "
            "URL is written to the book's identifiers when one isn't "
            "already set there -- an existing identifier is never "
            "overwritten. Applies regardless of which modes above are on.")
        self.add_identifier.setChecked(prefs[KEY_ADD_IDENTIFIER])
        layout.addWidget(self.add_identifier)

        self.preview = QCheckBox('Preview before writing', tab)
        self.preview.setToolTip(
            "Show a summary of everything that would be written -- across "
            "whichever modes are enabled above -- for review before "
            "writing anything.")
        self.preview.setChecked(prefs[KEY_PREVIEW])
        layout.addWidget(self.preview)

        self.show_confirmation = QCheckBox('Show confirmation after writing', tab)
        self.show_confirmation.setToolTip(
            "Show a small popup summarizing how many books were updated "
            "after writing finishes. Uncheck to skip it and return "
            "straight to Calibre.")
        self.show_confirmation.setChecked(prefs[KEY_SHOW_CONFIRMATION])
        layout.addWidget(self.show_confirmation)

        layout.addStretch(1)
        return tab

    def _build_mode1_group(self, prefs, custom_columns):
        group = QGroupBox('Save all extracted metadata', self)
        group.setCheckable(True)
        group.setChecked(prefs[KEY_MODE1_ENABLED])
        group.setToolTip(
            "Stages a FanFicFare-format metadata blob in a custom column, "
            "for FanFicFare's own \"Update Calibre Metadata from Saved "
            "Metadata Column\" action to read back later. Does not touch "
            "your library's Title/Tags/etc. directly.")
        self.mode1_group = group

        subtext = _subtext_label(
            '(Raw metadata in one column for FanFicFare processing)', self)

        col_row = QHBoxLayout()
        label = QLabel('Saved Metadata Column:')
        tooltip = (
            'The custom column to write recovered metadata into. Must be a '
            "Long Text column -- point this at the same column FanFicFare's "
            'own "Saved Metadata Column" setting uses, so its "Update '
            'Calibre Metadata from Saved Metadata Column" action can read '
            'it back.\n(Long Text columns only.)'
        )
        label.setToolTip(tooltip)
        col_row.addWidget(label)

        self.dest_column = QComboBox(self)
        self.dest_column.setToolTip(tooltip)
        self.dest_column.addItem('', '')
        for key, column in sorted(custom_columns.items()):
            if column['datatype'] == 'comments':
                self.dest_column.addItem(column['name'], key)
        _add_other_library_column(self.dest_column, prefs[KEY_DEST_COLUMN], custom_columns)
        idx = self.dest_column.findData(prefs[KEY_DEST_COLUMN])
        self.dest_column.setCurrentIndex(idx if idx >= 0 else 0)
        col_row.addWidget(self.dest_column)

        self.overwrite = QCheckBox('Overwrite existing Saved Metadata', self)
        self.overwrite.setToolTip(
            "If unchecked, books whose Saved Metadata column already has a "
            "value are skipped rather than overwritten.")
        self.overwrite.setChecked(prefs[KEY_OVERWRITE])
        self.saved_column_note = _subtext_label('', self)

        inner = QVBoxLayout()
        inner.addWidget(subtext)
        inner.addLayout(col_row)
        inner.addWidget(self.saved_column_note)
        inner.addWidget(self.overwrite)
        group.setLayout(inner)
        return group

    def _build_mode2_group(self, prefs):
        group = QGroupBox('Update standard Calibre metadata', self)
        group.setCheckable(True)
        group.setChecked(prefs[KEY_MODE2_ENABLED])
        group.setToolTip(
            "Writes directly into your library's Title/Author/Tags/Series/"
            "Comments fields, using FanFicFare's own default AO3 field "
            "composition rules -- no need to also run FanFicFare's Update "
            "Calibre Metadata action. This modifies your library directly, "
            "not just a staging column.")
        self.mode2_group = group

        subtext = _subtext_label('(Title, Author, Tags, Series, Comments...)', self)

        self.mode2_overwrite = QCheckBox('Overwrite existing standard metadata', self)
        self.mode2_overwrite.setToolTip(
            "If unchecked, a field already populated in Calibre (e.g. an "
            "existing Title or Tags) is left alone rather than overwritten. "
            "Blank publication dates and Calibre's Unknown author are filled in.")
        self.mode2_overwrite.setChecked(prefs[KEY_MODE2_OVERWRITE])

        self.anthology_pubdate = QCheckBox(
            'For anthologies, set Published to the earliest story\'s date', self)
        self.anthology_pubdate.setToolTip(
            "Anthologies have no publication date of their own. If checked, "
            "Published is set to the earliest date among the anthology's "
            "stories, as FanFicFare does for its anthologies.")
        self.anthology_pubdate.setChecked(prefs[KEY_ANTHOLOGY_PUBDATE])

        inner = QVBoxLayout()
        inner.addWidget(subtext)
        inner.addWidget(self.mode2_overwrite)
        inner.addWidget(self.anthology_pubdate)
        group.setLayout(inner)
        return group

    def _build_mode3_group(self, prefs, custom_columns):
        group = QGroupBox('Update custom columns', self)
        group.setCheckable(True)
        group.setChecked(prefs[KEY_MODE3_ENABLED])
        group.setToolTip(
            "Writes specific recovered fields into custom columns you "
            "choose, e.g. a Fandom column or a Words column. This modifies "
            "your library directly, not just a staging column.")
        self.mode3_group = group
        self.column_mapping = dict(prefs[KEY_COLUMN_MAPPING])
        self.anthology_fields = dict(prefs[KEY_ANTHOLOGY_FIELDS])
        self.custom_overwrite = dict(prefs[KEY_CUSTOM_OVERWRITE])

        subtext = _subtext_label(
            "(Map extracted data directly to your own columns - useful if "
            "you don't use FanFicFare)", self)

        configure_button = QPushButton('Configure column mapping…', self)
        configure_button.clicked.connect(lambda: self._open_column_mapping(custom_columns))
        self.mode3_summary = QLabel(self)
        self._update_mode3_summary()

        inner = QVBoxLayout()
        inner.addWidget(subtext)
        inner.addWidget(configure_button)
        inner.addWidget(self.mode3_summary)
        group.setLayout(inner)
        return group

    def _open_column_mapping(self, custom_columns):
        dialog = ColumnMappingDialog(self, custom_columns, self.column_mapping,
                                     reserved_column=self.dest_column.currentData(),
                                     anthology_fields=self.anthology_fields,
                                     overwrite_fields=self.custom_overwrite)
        if dialog.exec() == ColumnMappingDialog.DialogCode.Accepted:
            self.column_mapping = dialog.mapping()
            self.anthology_fields = dialog.anthology_fields()
            self.custom_overwrite = dialog.overwrite_fields()
            self._update_mode3_summary()
            self._refresh_saved_columns()

    def _update_mode3_summary(self):
        n = len(self.column_mapping)
        elsewhere = sum(1 for key in self.column_mapping if key not in self.custom_columns)
        self.mode3_summary.setText(
            '%d column%s mapped%s.' % (n, '' if n == 1 else 's',
                                       ' (%d not in this library)' % elsewhere if elsewhere else ''))

    def save_settings(self):
        prefs = get_prefs()
        prefs[KEY_MODE1_ENABLED] = self.mode1_group.isChecked()
        prefs[KEY_DEST_COLUMN] = self.dest_column.itemData(self.dest_column.currentIndex())
        prefs[KEY_OVERWRITE] = self.overwrite.isChecked()
        prefs[KEY_MODE2_ENABLED] = self.mode2_group.isChecked()
        prefs[KEY_MODE2_OVERWRITE] = self.mode2_overwrite.isChecked()
        prefs[KEY_MODE3_ENABLED] = self.mode3_group.isChecked()
        prefs[KEY_COLUMN_MAPPING] = self.column_mapping
        prefs[KEY_ANTHOLOGY_FIELDS] = self.anthology_fields
        prefs[KEY_CUSTOM_OVERWRITE] = self.custom_overwrite
        prefs[KEY_ANTHOLOGY_PUBDATE] = self.anthology_pubdate.isChecked()
        prefs[KEY_ADD_IDENTIFIER] = self.add_identifier.isChecked()
        prefs[KEY_PREVIEW] = self.preview.isChecked()
        prefs[KEY_SHOW_CONFIRMATION] = self.show_confirmation.isChecked()
        plugin_prefs[STORE_NAME] = prefs
