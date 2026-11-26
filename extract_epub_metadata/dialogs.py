from qt.core import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QListWidget, QListWidgetItem, QPlainTextEdit,
    QEvent, QPoint, QScrollArea, QSplitter, Qt, QVBoxLayout, QWidget,
)

from calibre_plugins.extract_epub_metadata.calibre_fields import (
    ALL_METADATA_KEYS, ANTHOLOGY_HELP, ANTHOLOGY_PAIRS, ANTHOLOGY_RATING_ALL, ANTHOLOGY_RATING_HIGHEST,
    compatible_columns_for_key, field_help, field_label,
)
from calibre_plugins.extract_epub_metadata.anthology import format_summary, story_detail_lines
from calibre_plugins.extract_epub_metadata.extractors._text import html_to_text


def _format_field_dict(fields, sources=None):
    lines = []
    for key in sorted(fields):
        value = fields[key]
        if key in ('description', 'comments') and isinstance(value, str):
            value = html_to_text(value)
        if isinstance(value, list):
            value = '; '.join(str(v) for v in value)
        if sources is not None:
            lines.append('  %s [%s]: %s' % (key, sources.get(key, 'derived'), value))
        else:
            lines.append('  %s: %s' % (key, value))
    return lines


# Plain names for the preview; FanFicFare calls these anthologies.
_ANTHOLOGY_TYPES = {'epubmerge anthology': 'FanFicFare anthology',
                    'series collection': 'series EPUB'}


class BookResult:
    """One book's outcome from the extraction/mapping/serialization pipeline.
    `blob` and `standard_fields` are only populated for modes that are
    actually enabled for this run (empty/falsy otherwise), so
    summary_lines() only shows sections for what will actually happen."""

    def __init__(self, book_id, title, fields, sources, blob,
                 identifier_url=None, identifier_already_set=False,
                 existing_column_value=None, standard_fields=None,
                 custom_column_values=None, error=None, standard_skipped=None,
                 saved_write=None, notes=None, identifier_requested=True,
                 custom_skipped=None, custom_fill_only=None, standard_unchanged=None,
                 custom_unchanged=None, saved_unchanged=False, saved_requested=True,
                 standard_requested=True, custom_requested=True):
        self.book_id = book_id
        self.title = title
        self.fields = fields
        self.sources = sources
        self.blob = blob
        self.identifier_url = identifier_url
        self.identifier_already_set = identifier_already_set
        self.existing_column_value = existing_column_value
        self.standard_fields = standard_fields or {}
        self.custom_column_values = custom_column_values or {}
        self.error = error
        self.standard_skipped = standard_skipped or {}
        self.custom_skipped = custom_skipped or {}
        self.custom_fill_only = set(custom_fill_only or ())
        # Values Calibre already holds: shown as up to date, never written.
        self.standard_unchanged = standard_unchanged or {}
        self.custom_unchanged = custom_unchanged or {}
        self.saved_unchanged = saved_unchanged
        self.saved_requested = saved_requested
        self.standard_requested = standard_requested
        self.custom_requested = custom_requested
        self.saved_write = bool(blob) if saved_write is None else saved_write
        self.notes = notes or []
        self.identifier_requested = identifier_requested
        self.write_errors = []
        self.written_fields = []

    @property
    def has_writes(self):
        return bool(not self.error and (self.saved_write or self.standard_fields or
                    self.custom_column_values or
                    (self.identifier_url and not self.identifier_already_set)))

    @property
    def has_unchanged(self):
        return bool(self.standard_unchanged or self.custom_unchanged or self.saved_unchanged)

    def overview_lines(self):
        """A short block at the top of the preview: what was found and what
        will happen, per write option, then whether anything will be written."""
        def counts(label, to_write, kept, unchanged, kept_reason):
            found = len(to_write) + len(kept) + len(unchanged)
            if not found:
                return '%s: nothing found' % label
            parts = ['%d found' % found, '%d to write' % len(to_write)]
            if unchanged:
                parts.append('%d already up to date' % len(unchanged))
            if kept:
                parts.append('%d kept (%s)' % (len(kept), kept_reason))
            return '%s: %s' % (label, ', '.join(parts))

        collection = self.fields.get('collectionType')
        lines = []
        if self.standard_requested:
            lines.append(counts('Standard fields', self.standard_fields, self.standard_skipped,
                                self.standard_unchanged, 'overwrite is off'))
        if self.custom_requested:
            lines.append(counts('Custom columns', self.custom_column_values, self.custom_skipped,
                                self.custom_unchanged, 'Overwrite not ticked'))
        if self.saved_requested:
            if collection:
                state = 'not used for anthologies'
            elif not self.blob:
                state = 'skipped, no supported story URL'
            elif self.saved_write:
                state = 'will be written'
            elif self.saved_unchanged:
                state = 'already up to date'
            else:
                state = 'kept (overwrite is off)'
            lines.append('Saved Metadata: %s' % state)
        if self.identifier_url and not self.identifier_already_set:
            lines.append('Story URL identifier: will be added')
        changes = (len(self.standard_fields) + len(self.custom_column_values) + int(bool(self.saved_write))
                   + int(bool(self.identifier_url and not self.identifier_already_set)))
        if self.has_writes:
            lines.append('>> Ready to write %d change%s.' % (changes, '' if changes == 1 else 's'))
        elif self.has_unchanged:
            lines.append('>> Nothing to write: everything is already up to date.')
        else:
            lines.append('>> Nothing to write with the current settings.')
        rule = '=' * 44
        return [rule] + lines + [rule, '']

    def summary_lines(self):
        if self.error:
            return ['Error: %s' % self.error]
        lines = self.overview_lines() + list(self.notes)
        collection = self.fields.get('collectionType')
        if collection:
            lines.extend(['Anthology type: %s' % _ANTHOLOGY_TYPES.get(collection, collection),
                          'Anthology URL: %s' % self.fields.get('collectionUrl', 'not recovered')])
            if self.saved_requested:
                lines.append('Saved Metadata skipped: FanFicFare imports single stories, not anthologies.')
        if self.identifier_url:
            note = ' (already set, not changed)' if self.identifier_already_set else ' (will be added)'
            lines.append('Story URL identifier: %s%s' % (self.identifier_url, note))
        elif not collection and self.identifier_requested:
            lines.append('Story URL identifier: not recovered -- FanFicFare '
                          'may not be able to pick an adapter for this book.')

        if self.standard_fields or self.standard_skipped or self.standard_unchanged:
            lines.append('')
            lines.append('=== Standard Calibre Fields ===')
            lines.extend(_format_field_dict(self.standard_fields))
            if self.standard_skipped:
                lines.append('Existing values kept; these fields will be skipped:')
                lines.extend(_format_field_dict(self.standard_skipped))
            if self.standard_unchanged:
                lines.append('Already up to date; nothing to write:')
                lines.extend(_format_field_dict(self.standard_unchanged))

        if self.custom_column_values or self.custom_skipped or self.custom_unchanged:
            lines.append('')
            lines.append('=== Custom Column Mapping ===')
            lines.extend(_format_field_dict(self.custom_column_values))
            if self.custom_skipped:
                lines.append('Existing values kept; these columns will be skipped:')
                lines.extend(_format_field_dict(self.custom_skipped))
            if self.custom_unchanged:
                lines.append('Already up to date; nothing to write:')
                lines.extend(_format_field_dict(self.custom_unchanged))

        if self.blob:
            lines.extend(['', '=== Saved Metadata Column ===',
                          'Will be written.' if self.saved_write else
                          'Already up to date; nothing to write.' if self.saved_unchanged else
                          'Existing column value kept; Saved Metadata will be skipped.'])
            lines.append('Recovered fields (source tier in brackets):')
            lines.extend(_format_field_dict(self.fields, self.sources))

        if collection:
            lines.extend(['', '=== Recovered Anthology Facts ==='])
            lines.extend(_format_field_dict(
                {k: v for k, v in self.fields.items()
                 if k not in ('collectionRecords', 'collectionType', 'collectionStoryReport')},
                self.sources))
            records = self.fields.get('collectionRecords', [])
            if records:
                lines.extend(['', '=== Individual Stories ===', format_summary(records)])
                lines.extend(story_detail_lines(records))
            else:
                lines.append('Individual story metadata is not available in this EPUB.')
        if not self.has_writes and self.has_unchanged:
            lines.extend(['', 'Everything is already up to date; nothing will be written.'])
        elif not self.has_writes:
            lines.extend(['', 'No changes will be written with the current settings.'])
            if collection:
                lines.append('Enable standard/custom-column updates, or map the Anthology Story Report '
                             'field for embedded story details.')

        return lines


class PreviewDialog(QDialog):
    """Summary of recovered metadata for one or more books, with a
    checkbox per book to include/exclude it from the write, shown before
    anything is actually written."""

    def __init__(self, gui, results):
        QDialog.__init__(self, gui)
        self.setWindowTitle('Extract Fanfic Metadata -- Preview')
        self.resize(760, 480)
        self.results = results

        layout = QVBoxLayout(self)

        intro = QLabel('Review metadata found in the book. Existing values are kept unless '
                       'overwriting is enabled. Skipped fields are labelled below. '
                       'Uncheck any book to skip it.')
        intro.setWordWrap(True)
        layout.addWidget(intro)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        layout.addWidget(splitter, 1)

        self.list_widget = QListWidget(splitter)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        for result in results:
            item = QListWidgetItem(result.title or ('Book %s' % result.book_id))
            eligible = result.has_writes
            if eligible:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if eligible else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, result)
            if result.error:
                item.setToolTip(result.error)
            self.list_widget.addItem(item)
        self.list_widget.currentItemChanged.connect(self._show_details)

        self.details = QPlainTextEdit(splitter)
        self.details.setReadOnly(True)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Write Selected')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.write_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.list_widget.itemChanged.connect(self._update_write_button)
        self._update_write_button()

        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def _show_details(self, current, _previous):
        if current is None:
            self.details.setPlainText('')
            return
        result = current.data(Qt.ItemDataRole.UserRole)
        self.details.setPlainText('\n'.join(result.summary_lines()))

    def _update_write_button(self, *_):
        self.write_button.setEnabled(bool(self.selected_results()))

    def selected_results(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            result = item.data(Qt.ItemDataRole.UserRole)
            if item.checkState() == Qt.CheckState.Checked and result.has_writes:
                selected.append(result)
        return selected


OVERWRITE_TIP = "Replace a value already in this column. Off: only fill it when it's empty."


class ColumnMappingDialog(QDialog):
    """Mode 3 config: one row per recoverable metadata field (as a static
    label, with a tooltip explaining it), each with a dropdown of the
    custom columns compatible with that field
    (calibre_fields.py::compatible_columns_for_key). Fields with no
    compatible column in this library aren't shown."""

    def __init__(self, gui, custom_columns, current_mapping, reserved_column=None,
                 anthology_fields=None, overwrite_fields=None):
        QDialog.__init__(self, gui)
        self.setWindowTitle('Extract Fanfic Metadata -- Custom Column Mapping')
        self.resize(800, 460)
        anthology_fields = anthology_fields or {}
        overwrite_fields = overwrite_fields or {}
        # Settings are shared by every library. Keep what this library can't
        # show: mappings to columns it doesn't have, and ticks for fields with
        # no row here, so pressing OK doesn't drop them for other libraries.
        self._other_library_mapping = {column_key: metadata_key
                                       for column_key, metadata_key in current_mapping.items()
                                       if column_key not in custom_columns}
        self._previous_anthology_fields = dict(anthology_fields)
        self._previous_overwrite_fields = dict(overwrite_fields)

        # current_mapping is {column_key: metadata_key} (matches how it's
        # stored/consumed elsewhere) -- invert it once for O(1) lookup of
        # "what column, if any, is this field currently mapped to".
        column_for_key = {v: k for k, v in current_mapping.items()}

        layout = QVBoxLayout(self)

        intro = QLabel(
            'Choose which column each extracted field should be written '
            'to. Empty or not mapped fields will be skipped. '
            'The Saved Metadata column is reserved for raw metadata.\n'
            'Tick "Overwrite" to replace a value already in that column; '
            'unticked columns are only filled when empty.\n'
            'Tick "Anthologies too" to fill that column for anthologies as well, '
            'with the value for the whole anthology.')
        intro.setWordWrap(True)
        layout.addWidget(intro)
        header_slot = layout.count()

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        form_widget = QWidget(scroll)
        form = QGridLayout(form_widget)
        form.setColumnStretch(1, 1)
        margins = form.contentsMargins()
        # The zero-height heading row still gets one row of spacing; take it back.
        form.setContentsMargins(margins.left(), max(0, margins.top() - max(form.verticalSpacing(), 0)),
                                margins.right() + 16, margins.bottom())

        # The dropdown lists every column compatible by *datatype* alone
        # (calibre_fields.py::compatible_columns_for_key doesn't try to
        # guess semantic relevance), so e.g. a "chapters" text column
        # shows up as a candidate for "Category" too, not just "Chapters
        # (Downloaded/Total)" -- confusing without a clear header
        # distinguishing "this plugin's field" from "your column".
        # Headings stay visible while the rows scroll: zero-height copies in
        # row 0 size and place each grid column, and the visible headings in
        # a bar above the scroll area are moved to match them.
        self.header_bar = QWidget(self)
        header_texts = ('Extracted Field', 'Write To Column', 'Overwrite', 'Anthologies too')
        placeholders, self.header_labels = [], []
        for text in header_texts:
            for parent, target in ((form_widget, placeholders), (self.header_bar, self.header_labels)):
                header = QLabel(text, parent)
                font = header.font()
                font.setBold(True)
                header.setFont(font)
                if text == 'Overwrite':
                    header.setToolTip(OVERWRITE_TIP)
                target.append(header)
        for header in placeholders:
            header.setMaximumHeight(0)
        self.header_placeholders = placeholders
        self.header_bar.setFixedHeight(max(h.sizeHint().height() for h in self.header_labels))
        header_field, header_column, header_overwrite, header_anthology = placeholders
        form.addWidget(header_field, 0, 0)
        form.addWidget(header_column, 0, 1)
        center = Qt.AlignmentFlag.AlignHCenter
        form.setHorizontalSpacing(max(form.horizontalSpacing(), 0) + 12)
        form.addWidget(header_overwrite, 0, 2, center)
        form.addWidget(header_anthology, 0, 3, center)
        self.anthology_controls = {}
        self.overwrite_controls = {}

        self.rows = []
        custom_columns = {k: v for k, v in custom_columns.items() if k != reserved_column}
        column_names = {key: col['name'] for key, col in custom_columns.items()}
        for metadata_key in sorted(ALL_METADATA_KEYS, key=field_label):
            column_keys = compatible_columns_for_key(metadata_key, custom_columns)
            if not column_keys:
                continue

            combo = QComboBox(form_widget)
            combo.addItem('(not mapped)', '')
            for column_key in sorted(column_keys, key=lambda ck: column_names[ck]):
                combo.addItem(column_names[column_key], column_key)
            idx = combo.findData(column_for_key.get(metadata_key, ''))
            combo.setCurrentIndex(idx if idx >= 0 else 0)

            label = QLabel(field_label(metadata_key) + ':', form_widget)
            help_text = field_help(metadata_key)
            if help_text:
                label.setToolTip(help_text)
                combo.setToolTip(help_text)

            row = len(self.rows) + 1
            form.addWidget(label, row, 0)
            form.addWidget(combo, row, 1)
            control = self._anthology_control(metadata_key, anthology_fields.get(metadata_key),
                                              form_widget)
            if control is not None:
                form.addWidget(control, row, 3,
                               center if isinstance(control, QCheckBox) else Qt.AlignmentFlag(0))
                self.anthology_controls[metadata_key] = control
            overwrite = QCheckBox(form_widget)
            overwrite.setChecked(bool(overwrite_fields.get(metadata_key)))
            overwrite.setToolTip(OVERWRITE_TIP)
            form.addWidget(overwrite, row, 2, center)
            self.overwrite_controls[metadata_key] = overwrite
            self.rows.append((metadata_key, combo))

        form.setRowStretch(len(self.rows) + 1, 1)
        form_widget.setLayout(form)
        scroll.setWidget(form_widget)
        layout.insertWidget(header_slot, self.header_bar)
        layout.addWidget(scroll, 1)
        form_widget.installEventFilter(self)
        self.header_bar.installEventFilter(self)

        if not self.rows:
            self.header_bar.hide()
            layout.addWidget(QLabel(
                'No custom columns with a supported datatype found. Create '
                'one in Preferences → Add your own columns first.'))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Move, QEvent.Type.LayoutRequest,
                            QEvent.Type.Show):
            self._place_headers()
        return super().eventFilter(watched, event)

    def _place_headers(self):
        bar_x = self.header_bar.mapTo(self, QPoint(0, 0)).x()
        for placeholder, label in zip(self.header_placeholders, self.header_labels):
            x = placeholder.mapTo(self, QPoint(0, 0)).x() - bar_x
            label.setGeometry(x, 0, max(placeholder.width(), label.sizeHint().width()),
                              self.header_bar.height())

    @staticmethod
    def _anthology_control(metadata_key, current, parent):
        if metadata_key not in ANTHOLOGY_PAIRS:
            return None
        tip = ANTHOLOGY_HELP.get(metadata_key, 'For anthologies: the value for the whole anthology.')
        tip += '\nOff: this column stays empty for anthologies.'
        if metadata_key == 'rating':
            control = QComboBox(parent)
            control.addItem("Don't fill", '')
            control.addItem('Highest', ANTHOLOGY_RATING_HIGHEST)
            control.addItem('All (comma separated)', ANTHOLOGY_RATING_ALL)
            control.setCurrentIndex(max(0, control.findData(current or '')))
            control.setToolTip(tip)
            return control
        control = QCheckBox(parent)
        control.setChecked(bool(current))
        control.setToolTip(tip)
        return control

    def anthology_fields(self):
        result = {}
        for metadata_key, control in self.anthology_controls.items():
            if isinstance(control, QComboBox):
                value = control.currentData()
                if value:
                    result[metadata_key] = value
            elif control.isChecked():
                result[metadata_key] = True
        result.update({key: value for key, value in self._previous_anthology_fields.items()
                       if key not in self.anthology_controls})
        return result

    def overwrite_fields(self):
        result = {metadata_key: True for metadata_key, control in self.overwrite_controls.items()
                  if control.isChecked()}
        result.update({key: value for key, value in self._previous_overwrite_fields.items()
                       if key not in self.overwrite_controls})
        return result

    def mapping(self):
        result = dict(self._other_library_mapping)
        for metadata_key, combo in self.rows:
            column_key = combo.itemData(combo.currentIndex())
            if column_key:
                result[column_key] = metadata_key
        return result

    def accept(self):
        selected = [combo.currentData() for _, combo in self.rows if combo.currentData()]
        if len(selected) != len(set(selected)):
            from calibre.gui2 import error_dialog
            error_dialog(self, 'Conflicting mappings',
                         'Each destination column can receive only one extracted field. '
                         'Choose a different column for duplicate destinations.', show=True)
            return
        super().accept()
