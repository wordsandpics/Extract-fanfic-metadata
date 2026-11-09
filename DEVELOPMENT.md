# Format notes and testing

Technical reference for maintainers. For installation and everyday use, see the
[README](README.md). For the public synthetic examples, see the
[fixture catalogue](FIXTURE-INVENTORY.md).

## Supported EPUBs

The plugin is built and tested primarily with Archive of Our Own (AO3) EPUBs, including downloads made with [ao3downloader](https://github.com/nianeyna/ao3downloader). It also supports:

- fanfiction.net EPUBs from [fichub.net](https://fichub.net) and the [WebToEpub browser extension](https://github.com/dteviot/WebToEpub)
- FicLab fanfiction.net EPUBs, checked against four downloads from versions 1.0.111 and 1.0.113
- AO3 EPUBs from ficdownloader and [AO3 Saver](https://ao3saver.com)
- AO3 works saved from a [Wayback Machine](https://web.archive.org) snapshot using WebToEpub or [Save as eBook](https://chromewebstore.google.com/detail/save-as-ebook/haaplkpoiimngbppjihnegfmpejdnffj)
- AO3 PDF downloads converted to EPUB
- EPUBs with a clearly labelled opening header from a PDF conversion, for a limited set of fields

For Save as eBook, save the work’s **Entire Work** snapshot (`?view_full_work=true`); otherwise, the EPUB may contain only the chapter currently on screen.

Other sites and EPUB layouts may work, but haven’t been tested. The plugin skips metadata it can’t confidently recognize, so always review the preview before writing.

### FanFicFare title pages

A FanFicFare title page has no Fandom line. For AO3 and fanfiction.net its
Category holds the fandoms, so it fills Fandom(s) when no other source gives one.
Other sites use Category for their own labels, so it stays Category only.

Series, Series URL and Author URL are read from the title page too. Shared
FanFicFare files may record them nowhere else. Series is used only in
FanFicFare's `Name [N]` form, and the URLs only when they are links.

### ficdownloader

ficdownloader EPUBs (OPF generator "Ebook-lib") list AO3 metadata on an "About"
page as labelled lines (`<span class="metadata-label">`), followed by Summary
and Notes headings. The tool leaves some values out: a single fandom or
relationship, and the "No Archive Warnings Apply" warning. Those stay empty;
nothing is filled in. The story link comes from the page's Source line, since
the OPF identifier has no `https://`.

### AO3 Saver

AO3 Saver EPUBs carry an AO3-style preface but record the AO3 Saver mirror
address (`ao3saver.com/works/…`) as the source. The preface's original AO3 link
is used instead, so FanFicFare can update the story. The byline is a plain
`by <a>…</a>` line without AO3's author markup; co-authors and pseuds are read
from it, and "Inspired by" credits are excluded.

### FicLab metadata

FicLab's labeled summary table supplies story word/chapter counts, completion
status, and rating. Explicit copyright-page profile links supply author URLs and
IDs when they match the book's author names. Mixed tags are retained as ordinary
tags; the plugin does not guess which are fandoms, characters, or genres.

**Word Count uses the summary's story count.** FicLab's internal EPUB extent count
differs in all four samples; it is used only when the summary has no word count.
An invalid or conflicting summary count is left unset rather than silently
replaced with the other count.

Publication/update timestamps retain their recorded time-zone offsets. Calibre
may display them in local time: for example, December 29, 2012 at 23:59:29 UTC
is December 30 in UTC+01:00. The synthetic timestamp-day-boundary example covers
this case. If timestamps are missing,
the reader can use FicLab's displayed English dates without inventing an offset.
FanFicFare's Saved Metadata reader cannot load offsets in its date fields. Those
fields use UTC without an offset suffix; the saved record also keeps the original
offset-bearing timestamps as text. Calibre's direct standard/custom writes retain
the full timestamps.
Other FicLab source sites, ongoing works, and altered layouts have not yet been
checked with real samples.

## Direct AO3 PDF input

For books without EPUB or TXT, the reader uses Calibre's bundled `pdftohtml` to
inspect at most five opening pages (30-second timeout; 2 MiB XML limit). No OCR,
online requests or full-book conversion is performed. A recognizable AO3 download
notice, labeled header, title and byline are required. Browser printouts and
image-only pages are rejected with an explanation.

Printed positions rejoin table labels and wrapped text. Explicit fields supply
names, counts, dates and tags; profile URLs must match the byline. Separate series
entries are preserved. A summary needs a clear section/heading boundary; ambiguous
or unbounded values are omitted with a partial-recovery note. PDF generation dates
are not story dates. Source order is EPUB, TXT, PDF; a damaged preferred format
never silently triggers fallback.

Build the invented PDF examples with `python3 tests/build_pdf_fixtures.py`.
`tests/test_pdf.py` checks recognition and ambiguity without Calibre. In an explicit
temporary Calibre configuration with the plugin and FanFicFare installed, run
`calibre-debug -e tests/calibre_pdf_smoke.py` with `QT_QPA_PLATFORM=offscreen`.
It checks actual PDF extraction, preview, independent write modes, Saved Metadata
loading and source preference in a temporary library.

## HTML converted to EPUB

Calibre imports HTML as ZIP. Convert that book to EPUB before running extraction.
The AO3 reader handles split/older download headers, summaries, plural Categories,
and saved-page bylines. Explicit story headers replace browser-style title metadata;
a clean edited OPF title keeps its priority. A page's story URL needs its own controls
(chapter, bookmark or comment links, or the share box) to identify exactly one work;
links in summaries, notes and story text are ignored. Unrelated author credits are not
bylines. Direct HTML/ZIP input and LiveJournal headers are not supported.

## Supported TXT archives

TXT files with this opening header structure are supported directly; conversion
to EPUB is not required:

```text
Story title

by Author name

Category: Fandom name
Language: English
Status: Completed
Published: 2013-02-18
Words: 1,234
Story URL: https://www.fanfiction.net/s/1234567/1/
Summary: The archive's summary, on a single line.

Chapter text begins here.
```

Explicit `Title:` and `Author:` labels also work. Recognition requires a title,
an author, and at least two additional factual labels. Fields are optional apart
from that minimum. Their order, capitalization, and surrounding spaces may vary.
Supported fields include category/fandom, genre, language, characters,
relationships/ships, warnings, status, published/updated/packaged dates, rating,
chapter count, word count, publisher, story URL, author URL, and summary/description.
`Word Count` and `Chapter Count` are accepted aliases.

For this compact format, the metadata block must be contiguous, with one
`Label: value` per line. The first blank or ordinary text line ends it. Its summary
must be on one line. Seven distinct fanfiction.net examples in English and Spanish
have been checked.

Two additional layouts are recognized separately:

- **Spaced archive headers:** title and author on one line (`Title by Author`),
  blank lines between labeled fields, wrapped values, and a separate Summary
  section. A repeated story title must mark the end of the summary before chapter
  text. Checked against three privately retained source examples. Wrapped relationship
  slashes are rejoined; OCR spelling and punctuation are preserved as supplied.
- **PDF-style prefaces:** an opening “Posted originally on…” notice with an AO3
  or SquidgeWorld work URL, labeled metadata, and a repeated title/byline before
  the summary. PDF-style `Category` means pairing category (such as M/M), while
  `Fandom` is kept separately. A summary is recovered only when a recognizable
  section heading marks its end. Explicit series positions and stats are supported;
  missing dates, status, chapter counts, and author URLs are not invented.

If PDF text separates labels and values into detached columns, only reliable
fields are recovered: title, explicit story URL, labeled dates/counts, and a bounded
summary. Author, language, rating, and tag fields are omitted; the preview explains
the partial recovery. Public synthetic examples cover both the detached-column
layout and the clearly labeled PDF layout, alongside private source-file checks.
Notice-heavy saved web pages with largely unlabelled metadata remain unsupported.

Only the first 64 KiB and 200 lines are inspected. UTF-8, BOM-marked UTF-16, and
Windows-1252 text are supported. Conflicting duplicate fields are omitted;
unrecognized layouts are skipped with an explanation. These readers do not cover
every TXT archive format. Status and dates describe the saved copy, not the story's
current state online. Missing URLs and damaged names are not reconstructed from
filenames. Without a supported story URL in the header or Calibre's existing
identifiers, Saved Metadata is skipped; standard metadata and mapped custom columns
remain available.

When a book has both EPUB and TXT, EPUB takes precedence. TXT is used only when
the book has no EPUB; an unreadable EPUB does not trigger a TXT fallback.

## Anthologies

**Extract Metadata** recognizes epubmerge anthologies and EPUBs whose primary URL is a series URL (series EPUBs); both are called anthologies, as in FanFicFare. A story that merely links to a series is still treated as an ordinary story.

Anthology title, authors, language, tags, and description come from the outer EPUB metadata. Embedded stories may provide individual authors, URLs, summaries, dates, statuses, and counts. WebToEpub series EPUBs may contain only a saved series page; in that case, the plugin uses explicit series totals and dates when available rather than inventing individual story details.

The ordinary **Word Count** mapping uses the total for the anthology. A calculated total is written only when every embedded story has a reliable count. Additional anthology fields include work count, completed count, unknown statuses, total chapters, anthology URL, and series dates. Internal field keys keep the `collection` prefix so saved mappings carry over.

FanFicFare’s Saved Metadata import expects one story URL, so Saved Metadata is skipped for anthologies. Use standard metadata or custom-column updates instead. Ratings, warnings, and summaries remain associated with individual stories rather than being combined into anthology-wide values.

Existing anthology identifiers are preserved. Anthology previews show which values will be written or kept; books with no eligible changes can’t be selected for writing.

### Anthology-wide values

FanFicFare builds its own anthology metadata (`merge_meta_books` in its plugin) by joining
list fields, keeping the earliest published and latest updated dates, adding up chapters and
words, and taking status only from the series page. The plugin follows those rules for the
"Also for anthologies" column-mapping choices (`ANTHOLOGY_PAIRS` in `calibre_fields.py`):

- **Status** is the single Completed/In-Progress tag on the outer EPUB. FanFicFare removes the
  stories' own status tags when merging and adds the series page's status, so that tag is the
  series status. No tag, or both, leaves Status empty; it is never worked out from the stories.
- **Fandoms, characters and relationships** come from each story's FanFicFare title page and are
  combined in first-appearance order without duplicates. Category supplies fandoms only for AO3
  and fanfiction.net, as for single stories. Genre is not used: on AO3 title pages FanFicFare
  mixes freeform tags with AO3 categories there. Calibre's Tags already come from the outer EPUB.
- **Rating, Highest** uses each site's scale (AO3: General Audiences < Teen And Up Audiences <
  Mature < Explicit; fanfiction.net: K < K+ < T < M < MA) and is empty when sites differ or any
  rating is missing or off the scale, including AO3's "Not Rated". **All** lists each rating once.
- **Published** for standard metadata is opt-in and uses the earliest story date.

Rows that aren't ticked stay empty for anthologies. Single stories ignore the ticks.

### Anthology Story Report

The `collectionStoryReport` field holds `format_summary()`'s text: a first line of the form
`N/M fics complete.`, an optional unknown-status line, then each story's status, chapter and
word counts, authors, URL and dates. Users parse this text with Calibre templates, so
`tests/test_pipeline.py` pins it; changing it is a breaking change. Long summaries, ratings
and warnings stay in the detailed preview. It is offered for Long text columns only.

Until 1.3.0 a separate "Extract story status from anthology" action wrote this report, with
its own settings tab. `prefs_migration.py` maps that action's column to the field once and
drops its settings; it leaves the mapping alone if the column is already used or is the Saved
Metadata column, and switches on custom-column updates only when the report is the sole mapping.

## Known limitations

- fanfiction.net crossover EPUBs made with WebToEpub currently recover only the last fandom in the site breadcrumb.
- Other sites and EPUB layouts may yield incomplete metadata. A field may be skipped without an error if its format isn’t recognized.
- The PDF-reflow fallback does not infer publication dates or completion status, and skips approximate counts such as `~3400`.
- For Wayback snapshots, the plugin uses the original story URL as the story URL and retains the snapshot URL separately as `waybackUrl`. Status and counts reflect the snapshot date. FanFicFare exposes `waybackUrl` to `personal.ini` templates only if you add it to `extra_valid_entries`.

Always review the preview before writing.

## Running tests

Run the standard-library test suite with:

```sh
python3 -m unittest discover -s tests -v
```

The suite runs without Calibre installed and uses only synthetic EPUB and TXT examples in `tests/fixtures/`. Their filenames and titles identify the test cases. No original stories or private files are required. An optional test also checks FanFicFare’s metadata loader when FanFicFare is installed.

See the [fixture catalogue](FIXTURE-INVENTORY.md). Recreate the examples with `python3 tests/build_fixtures.py`; this uses only the standard library and invented scenario data.


The plugin was renamed from Extract Epub Metadata in 1.2.1. The action name, settings file and import name keep the old form so existing toolbars and settings carry over.

For a real Calibre check, set `CALIBRE_CONFIG_DIRECTORY` to a configuration in a
**temporary folder**, install FanFicFare and a ZIP built from the contents of
`extract_epub_metadata/` there, then run `tests/calibre_smoke.py` using
`calibre-debug -e`. Set `QT_QPA_PLATFORM=offscreen` to keep its windows off screen.
The harness refuses to run against a regular configuration and creates a temporary
library. It checks EPUB and TXT previews, database writes, and FanFicFare imports.
Set `EXTRACT_METADATA_SCREENSHOTS` to an output folder to save preview screenshots.
