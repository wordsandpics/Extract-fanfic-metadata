"""One-time settings changes between plugin versions (pure, no Calibre import)."""

REPORT_KEY = 'collectionStoryReport'
MIGRATED_FLAG = 'anthologyReportMigrated'
# Settings of the former "Extract story status from anthology" action (before 1.3.0).
OLD_ANTHOLOGY_KEYS = ('anthologyDestColumn', 'anthologyOverwrite', 'anthologyPreview',
                      'anthologyShowConfirmation')


def migrate_anthology_report(options):
    """The separate anthology report action became the "Anthology Story
    Report" custom-column field in 1.3.0. Map the old report column to that
    field once, so existing reports keep updating. Returns (options, changed).

    The column is left unmapped when it is already used by another field or
    is the Saved Metadata column. "Update custom columns" is switched on only
    when the report is the sole mapping, so no other column starts being
    written unexpectedly.
    """
    if options.get(MIGRATED_FLAG):
        return options, False
    migrated = dict(options)
    mapping = dict(options.get('columnMapping') or {})
    dest = options.get('anthologyDestColumn') or ''
    if (dest and dest != options.get('destColumn') and dest not in mapping
            and REPORT_KEY not in mapping.values()):
        mapping[dest] = REPORT_KEY
        if not options.get('mode3Enabled') and len(mapping) == 1:
            migrated['mode3Enabled'] = True
    migrated['columnMapping'] = mapping
    for key in OLD_ANTHOLOGY_KEYS:
        migrated.pop(key, None)
    migrated[MIGRATED_FLAG] = True
    return migrated, True
