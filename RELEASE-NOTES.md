# Extract Fanfic Metadata 1.3.1

Support for more of the tools people are using to save AO3 stories.

## New

- **ficdownloader EPUBs** are now read: tags, series, chapters, dates, status, summary
  and the story link. ficdownloader itself leaves some values out (a single fandom or
  relationship, and "No Archive Warnings Apply"); those stay empty.
- **FanFicFare title pages:** the series, series link and author link are recovered when
  the file records them nowhere else. This is common in FanFicFare files shared online.

## Fixed

- **AO3 Saver EPUBs** now get their authors (co-authors listed separately), summary and
  the original AO3 link instead of the AO3 Saver address, so FanFicFare can update them.
  Run the plugin again on AO3 Saver books to fill these in.
