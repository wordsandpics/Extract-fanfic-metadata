# Extract Fanfic Metadata 1.4.2

See at a glance what the plugin will do.

## New

- **A summary at the top of each book's preview.** It shows how many standard fields and
  custom columns were found, how many will be written, kept or are already up to date, what
  happens to Saved Metadata, and whether anything will be written at all.
- **Already up to date.** Values Calibre already holds are listed as already up to date
  instead of as changes. A book with nothing new says so and can't be selected.
- After writing, the message also counts books that were already up to date.

## Changed

- **New installs start ready to use**, with **Update standard Calibre metadata** on and
  **Save all extracted metadata** off, so the first run works without choosing a column.
  Existing settings don't change.
- **New settings order:** standard metadata first, then custom columns, then Saved Metadata
  (for FanFicFare).

## Fixed

- **Settings and multiple libraries.** The plugin's settings are shared by all your
  libraries. Pressing OK in a library that lacks some of your columns no longer removes
  those column mappings, their ticks, or the Saved Metadata column for your other
  libraries. Such columns now show as "not in this library".
- The message after writing no longer says that anthologies don't receive Saved Metadata
  every time you update one. The preview mentions it only when Save all extracted metadata
  is on.
