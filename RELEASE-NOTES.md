# Extract Fanfic Metadata 1.3.1

Support for AO3's HTML downloads and more of the tools people are using to save AO3 stories.

## New

- **AO3 HTML downloads are read directly.** AO3 currently offers only HTML downloads.
  Add the .html file to Calibre as usual and run **Extract Metadata**: no need to convert
  to EPUB first. It fills in the real title and author (instead of Calibre's "Title -
  author - fandom" and "Unknown"), plus the summary, tags, series, counts, dates and AO3 link.
  Web pages saved from a browser and other HTML still need converting to EPUB first.
- **ficdownloader EPUBs** are now read: tags, series, chapters, dates, status, summary
  and the story link. ficdownloader itself leaves some values out (a single fandom or
  relationship, and "No Archive Warnings Apply"); those stay empty.
- **FanFicFare title pages:** the series, series link and author link are recovered when
  the file records them nowhere else. This is common in FanFicFare files shared online.

## Fixed

- **AO3 Saver EPUBs** now get their authors (co-authors listed separately), summary and
  the original AO3 link instead of the AO3 Saver address, so FanFicFare can update them.
  Run the plugin again on AO3 Saver books to fill these in.
