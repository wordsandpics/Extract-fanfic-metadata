
from calibre.gui2 import error_dialog, info_dialog
from calibre.gui2.actions import InterfaceAction
from qt.core import QMenu

from calibre_plugins.extract_epub_metadata.calibre_fields import (
    apply_custom_column_mapping, apply_standard_fields,
    compute_custom_column_values, compute_standard_fields, plan_custom_columns, plan_standard_fields,
    write_field,
)
from calibre_plugins.extract_epub_metadata.common_utils import plugin_icon
from calibre_plugins.extract_epub_metadata.config import (
    KEY_ADD_IDENTIFIER, KEY_ANTHOLOGY_FIELDS, KEY_ANTHOLOGY_PUBDATE, KEY_COLUMN_MAPPING,
    KEY_CUSTOM_OVERWRITE,
    KEY_DEST_COLUMN, KEY_MODE1_ENABLED, KEY_MODE2_ENABLED, KEY_MODE2_OVERWRITE,
    KEY_MODE3_ENABLED, KEY_OVERWRITE, KEY_PREVIEW, KEY_SHOW_CONFIRMATION, get_prefs,
)
from calibre_plugins.extract_epub_metadata.dialogs import BookResult, PreviewDialog
from calibre_plugins.extract_epub_metadata.extractors._urls import is_wayback_url
from calibre_plugins.extract_epub_metadata.mapping import (extract_fields, extract_txt_fields, extract_pdf_fields,
                                                           extract_html_fields)
from calibre_plugins.extract_epub_metadata.fff_support import fff_import_support, fff_support_url
from calibre_plugins.extract_epub_metadata.serialize import serialize_saved_metadata


class ExtractEpubMetadataAction(InterfaceAction):
    # Former plugin name, kept so existing toolbar placements still find this action.
    name = 'Extract Epub Metadata'
    action_spec = (
        'Extract Metadata', None,
        'Extract metadata from selected EPUBs, TXT archive headers or AO3 PDFs into Saved Metadata and/or standard/custom Calibre fields',
        (),
    )
    action_type = 'current'

    def genesis(self):
        self.qaction.setIcon(plugin_icon())
        self.qaction.triggered.connect(self.run)
        self.menu = QMenu(self.gui)
        self.menu.addAction('Extract Metadata', self.run)
        self.menu.addAction('Configure…', self.show_configuration)
        self.qaction.setMenu(self.menu)

    def show_configuration(self):
        self.interface_action_base_plugin.do_user_config(self.gui)

    def run(self):
        prefs = get_prefs()
        mode1_on, mode2_on, mode3_on = (
            prefs[KEY_MODE1_ENABLED], prefs[KEY_MODE2_ENABLED], prefs[KEY_MODE3_ENABLED])
        dest_column, column_mapping = prefs[KEY_DEST_COLUMN], prefs[KEY_COLUMN_MAPPING]
        db = self.gui.current_db.new_api
        custom_columns = self.gui.library_view.model().custom_columns
        if not any((mode1_on, mode2_on, mode3_on)):
            return error_dialog(self.gui, 'Nothing enabled',
                                'Enable at least one extraction mode in this plugin’s settings.', show=True)
        if mode3_on and dest_column and dest_column in column_mapping:
            return error_dialog(self.gui, 'Conflicting column settings',
                                'The Saved Metadata column cannot also be a custom mapping destination. '
                                'Choose a different destination in Configure column mapping.', show=True)
        book_ids = self.gui.library_view.get_selected_ids()
        if not book_ids:
            return error_dialog(self.gui, 'No books selected', 'Select one or more books first.', show=True)
        results = [self._process_book(db, book_id, dest_column, prefs, mode1_on, mode2_on,
                                      mode3_on, column_mapping, custom_columns) for book_id in book_ids]
        if prefs[KEY_PREVIEW]:
            dialog = PreviewDialog(self.gui, results)
            if dialog.exec() != PreviewDialog.DialogCode.Accepted:
                return
            selected = dialog.selected_results()
        else:
            selected = [r for r in results if not r.error and r.has_writes]
        written = self._write_results(db, dest_column, selected, mode1_on, mode2_on, mode3_on)
        self._refresh_library(selected)
        self._show_outcome(results, written, len(book_ids), prefs[KEY_SHOW_CONFIRMATION],
                           include_extraction_errors=not prefs[KEY_PREVIEW])

    def _process_book(self, db, book_id, dest_column, prefs, mode1_on, mode2_on,
                      mode3_on, column_mapping, custom_columns):
        title = 'Book %s' % book_id
        try:
            title = db.get_metadata(book_id).title or title
            if db.has_format(book_id, 'EPUB'):
                book_format, extractor = 'EPUB', extract_fields
            elif db.has_format(book_id, 'TXT'):
                book_format, extractor = 'TXT', extract_txt_fields
            elif db.has_format(book_id, 'PDF'):
                book_format, extractor = 'PDF', extract_pdf_fields
            elif db.has_format(book_id, 'ZIP'):
                # Calibre stores an added .html file as a ZIP book by default.
                book_format, extractor = 'ZIP', extract_html_fields
            elif db.has_format(book_id, 'HTML'):
                book_format = 'HTML'

                def extractor(stream):
                    return extract_html_fields(stream, is_zip=False)
            else:
                raise ValueError('No EPUB, TXT, PDF or AO3 HTML format available for this book.')
            with db.format(book_id, book_format, as_file=True) as stream:
                fields, sources = extractor(stream)
            if not fields:
                if book_format == 'TXT':
                    raise ValueError('No recognizable opening metadata header found in this TXT. '
                                     'Expected a supported archive header or PDF-style preface.')
                if book_format in ('ZIP', 'HTML'):
                    raise ValueError('No AO3 download header found in this HTML. Saved web pages and '
                                     'other HTML can be converted to EPUB in Calibre first.')
                if book_format == 'PDF':
                    raise ValueError('No recognizable AO3 download header found in the opening PDF pages. '
                                     'Browser printouts and scanned PDFs are not supported.')
                raise ValueError('No recoverable metadata found in this EPUB.')
            collection = bool(fields.get('collectionType'))
            identifiers = db.field_for('identifiers', book_id, default_value={}) or {}
            notes = []
            if 'txt_pdf_partial' in sources.values():
                notes.append('Partial TXT recovery: metadata labels are separated from their values. '
                             'Author, language, rating and tags were omitted because this damaged layout '
                             'cannot be assigned reliably. Explicit URL, dates and counts are retained.')
            if 'pdf_ao3_partial' in sources.values():
                notes.append('Partial PDF recovery: some opening metadata could not be read reliably '
                             'within the page limit. Ambiguous fields were omitted; review the preview.')
            support_url = fff_support_url(identifiers, fields.get('storyUrl'), prefs[KEY_ADD_IDENTIFIER])
            support = fff_import_support(support_url) if mode1_on and not collection else None
            save_enabled = mode1_on and not collection and support is not False
            if mode1_on and not collection:
                if support is False:
                    notes.append('Saved Metadata skipped: the URL FanFicFare will use is missing or unsupported. '
                                 'Use standard metadata or custom-column updates for this book.')
                elif support is None:
                    notes.append('FanFicFare support for this URL could not be checked. '
                                 'The Saved Metadata record may not be importable by FanFicFare.')
            if save_enabled and (not dest_column or dest_column not in custom_columns or
                                 custom_columns[dest_column]['datatype'] != 'comments'):
                raise ValueError('Choose a Long Text Saved Metadata column in settings, '
                                 'or disable Save all extracted metadata.')
            blob = serialize_saved_metadata(fields) if save_enabled else ''
            existing_value = None
            if save_enabled:
                existing_value = db.field_for(dest_column, book_id, default_value='') or None
            pending, skipped = plan_standard_fields(
                db, book_id, compute_standard_fields(fields, prefs[KEY_ANTHOLOGY_PUBDATE]),
                prefs[KEY_MODE2_OVERWRITE]
            ) if mode2_on else ({}, {})
            custom_values, custom_skipped, custom_fill_only = plan_custom_columns(
                db, book_id,
                compute_custom_column_values(fields, column_mapping, custom_columns,
                                             prefs[KEY_ANTHOLOGY_FIELDS]),
                column_mapping, custom_columns, prefs[KEY_CUSTOM_OVERWRITE],
            ) if mode3_on else ({}, {}, set())
            # A Wayback uri must not block adding the original work URL as url.
            uri = (identifiers.get('uri') or '').replace('|', ':')
            identifier_set = bool(identifiers.get('url') or (uri and not is_wayback_url(uri)))
            story_url = fields.get('storyUrl') if prefs[KEY_ADD_IDENTIFIER] and not collection else None
            return BookResult(
                book_id, title, fields, sources, blob, identifier_url=story_url,
                identifier_already_set=identifier_set, existing_column_value=existing_value,
                standard_fields=pending, standard_skipped=skipped, custom_column_values=custom_values,
                custom_skipped=custom_skipped, custom_fill_only=custom_fill_only,
                saved_write=bool(blob and (prefs[KEY_OVERWRITE] or not existing_value)),
                identifier_requested=prefs[KEY_ADD_IDENTIFIER],
                notes=notes,
            )
        except Exception as e:
            return BookResult(book_id, title, {}, {}, '', error='Failed to prepare metadata: %s' % e)

    def _write_results(self, db, dest_column, results, mode1_on, mode2_on, mode3_on):
        prefs = get_prefs()
        custom_columns = self.gui.library_view.model().custom_columns if mode3_on else {}
        written = 0
        for result in results:
            if result.error:
                continue
            result.written_fields, result.write_errors = [], []
            stage = 'Saved Metadata'
            try:
                if mode3_on and dest_column and (dest_column in result.custom_column_values or
                                                  dest_column in result.custom_skipped):
                    stage = 'Column settings'
                    raise ValueError('Saved Metadata column is reserved for raw metadata.')
                if mode1_on and result.saved_write and not result.fields.get('collectionType'):
                    if prefs[KEY_OVERWRITE] or not db.field_for(dest_column, result.book_id):
                        write_field(db, result.book_id, dest_column, result.blob, result.written_fields)
                if mode2_on:
                    for key, value in result.standard_fields.items():
                        stage = 'Standard field %s' % key
                        apply_standard_fields(db, result.book_id, {key: value},
                                              prefs[KEY_MODE2_OVERWRITE], result.written_fields)
                if mode3_on:
                    for key, value in result.custom_column_values.items():
                        stage = 'Custom column %s' % key
                        apply_custom_column_mapping(db, result.book_id, {key: value}, result.written_fields,
                                                    result.custom_fill_only, custom_columns)
                if result.identifier_url and not result.fields.get('collectionType'):
                    stage = 'Story URL identifier'
                    identifiers = db.field_for('identifiers', result.book_id, default_value={}) or {}
                    uri = (identifiers.get('uri') or '').replace('|', ':')
                    if not identifiers.get('url') and (not uri or is_wayback_url(uri)):
                        identifiers = dict(identifiers)
                        identifiers['url'] = result.identifier_url.replace(':', '|')
                        write_field(db, result.book_id, 'identifiers', identifiers, result.written_fields)
            except Exception as e:
                result.write_errors.append('%s: %s' % (stage, e))
            if result.written_fields:
                written += 1
        return written

    def _refresh_library(self, results):
        """Database writes do not repaint the library or update its book details."""
        book_ids = [result.book_id for result in results if result.written_fields]
        if book_ids:
            view = self.gui.library_view
            view.model().refresh_ids(book_ids, view.currentIndex().row())
            self.gui.tags_view.recount()

    def _show_outcome(self, results, written, total, show_confirmation, include_extraction_errors=False):
        summary = 'Updated %d of %d selected book(s).' % (written, total)
        failures = []
        for result in results:
            errors = list(result.write_errors)
            if include_extraction_errors and result.error:
                errors.append(result.error)
            if errors:
                progress = ('Changed fields: %s.' % ', '.join(result.written_fields)
                            if result.written_fields else 'No fields changed.')
                failures.append('%s (book %s): %s\n%s' %
                                (result.title, result.book_id, '; '.join(errors), progress))
        if failures:
            error_dialog(self.gui, 'Metadata update errors', summary,
                         det_msg='\n\n'.join(failures), show=True)
        elif show_confirmation:
            notes = []
            for result in results:
                if getattr(result, 'fields', {}).get('collectionType'):
                    notes.append('Anthologies do not receive FanFicFare Saved Metadata. '
                                 'Use standard/custom-column updates instead.')
                notes.extend(getattr(result, 'notes', []))
            if not written and notes:
                summary += '\n\n' + '\n'.join(dict.fromkeys(notes))
            info_dialog(self.gui, 'Extract Fanfic Metadata', summary,
                        det_msg='\n'.join(dict.fromkeys(notes)), show=True)
