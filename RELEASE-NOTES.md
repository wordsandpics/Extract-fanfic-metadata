# Extract Fanfic Metadata 1.3.0

This release makes the plugin friendlier to anthologies: EPUBs that bundle several
stories, usually made with FanFicFare's anthology feature.

## New

- **Your story columns can fill in for anthologies.** In **Configure column mapping…**,
  tick **Also for anthologies** on the fields you want. For an anthology they get:
  - **Status:** the series status recorded in the file. Left empty when none is recorded.
  - **Completed? (yes/no):** yes when the series is marked complete.
  - **Date Published / Date Updated:** the earliest and latest story dates.
  - **Chapter Count:** chapters across all stories, added up.
  - **Fandom(s), Characters, Relationship(s):** combined from every story.
  - **Rating:** the **Highest** rating, or **All** ratings, comma separated.

  All ticks are off by default, so nothing changes until you choose.
- **Published date for anthologies.** Under "Update standard Calibre metadata", you can
  set Published to the earliest story's date.

## Changed

- **The anthology report is now a column-mapping field,** **Anthology Story Report**, filled
  in the same run as everything else. Its text is unchanged. The separate **Extract story
  status from anthology** menu item and the **Anthology Status** settings tab are gone.
  If you used the report, your report column is added to the column mapping
  automatically. Mapped columns are refreshed on every run, so the report's own
  "Overwrite existing column value" setting no longer applies.
- **fanfiction.net ratings** are stored as FanFicFare stores them: "M" rather than
  "Fiction M", whichever tool saved the file.

## Fixed

- **Anthology Comments** written by "Update standard Calibre metadata" lost their line
  breaks. They now keep one story per line, as when Calibre imports the file. Run the
  plugin again on affected anthologies to restore the formatting.

See the [Settings and fields](https://github.com/wordsandpics/Extract-fanfic-metadata/blob/main/SETTINGS.md#anthologies)
guide for details.

## Install

Download **extract_fanfic_metadata-v1.3.0.zip** under Assets. In Calibre, open
**Preferences → Plugins → Load plugin from file**, select the ZIP, then restart.

If you still have the old **Extract Epub Metadata** installed, remove it in
**Preferences → Plugins** after installing. Your settings and toolbar button are kept.

## Notes

- Requires Calibre 6.0 or newer. Checked on Calibre 9.15 for macOS and in Calibre Zen.
  Windows and Linux were not rechecked.
- Anthology checks used FanFicFare-made AO3 series anthologies. Anthologies from other
  tools or sites may recover less.
