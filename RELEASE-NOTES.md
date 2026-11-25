# Extract Fanfic Metadata 1.4.1

Reads more FanFicFare title pages.

## Fixed

- **Optional AO3 lines on FanFicFare title pages.** If your FanFicFare adds Chapters/Total
  Chapters, Total Chapters, AO3 Categories and Freeform Tags to the title page, the plugin now
  reads them. Columns mapped to Chapter Count, AO3 Category (M/M, F/F, Gen…) and Additional
  Tags used to stay empty for these books.
- **Series from FanFicFare title pages.** FanFicFare writes the series as a link; the series
  and its link are now recovered.
- **Labels inside a summary.** A bold "Status:" or "Warnings:" typed in a story's summary no
  longer replaces the real value.
- **Anthology chapter totals** now include stories whose title page has only
  "Chapters/Total Chapters".
- **m.fanfiction.net links** are recognized as fanfiction.net.

## New

- **Subscribed, Bookmarked and Marked for Later.** Map them to Yes/No columns. They are read
  from the "I Subscribed", "I Bookmarked Story" and "I Marked for Later" lines that
  FanFicFare adds to the title page when it was logged in to AO3 and those entries are in its
  title-page list. They show the state on the day of the download, and books without the
  lines stay blank. They aren't filled for anthologies.

Books you already ran need to be extracted again to pick these up.
