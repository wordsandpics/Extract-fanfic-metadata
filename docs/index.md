---
layout: default
title: Add missing information to your saved fics in Calibre
subtitle: "Extract metadata from downloaded fic files and make them searchable"
permalink: /
---

<div class="intro" markdown="1">

You have a fic you saved a while ago. The fandom, relationships, tags and word count are written inside it, but much of that never reaches Calibre, so you can’t sort or search by it.

<figure class="inside-file">
  <img src="{{ '/assets/img/inside-the-file.png' | relative_url }}" alt="A story’s first page listing fandom, relationships, tags and word count; below it, Calibre shows only the author, format and summary">
  <figcaption>Top: the first page inside the file. Bottom: what Calibre shows for the same book.</figcaption>
</figure>

Maybe the story has since been deleted, AO3 is down, or you’d rather not add to the load on its servers. Extract Fanfic Metadata reads the information inside the file and adds it to your Calibre library. It works offline, without having to reach the original story.

Depending on the file, it can also find the author, summary, story link, chapters and more. It can write what it finds to Calibre’s standard fields or to your own custom columns.

</div>

<div class="callout note">
  <div class="callout-title">What you need</div>
  <ul>
    <li><strong>Calibre</strong>, version 6.0 or newer.</li>
    <li>Saved fanfiction already in your Calibre library: EPUB files, AO3’s own PDF and HTML downloads, and some text files. <a href="https://github.com/wordsandpics/Extract-fanfic-metadata#supported-files">See which files work</a>.</li>
    <li>FanFicFare is optional.</li>
  </ul>
  <p>Calibre, FanFicFare and the plugin are free.</p>
  <p>New to Calibre? Start with <a href="https://wordsandpics.github.io/fff-basics-tutorial/">FFF basics</a>.</p>
</div>

## 1. Install the plugin {#install}

1. Open the [latest release](https://github.com/wordsandpics/Extract-fanfic-metadata/releases/latest). Under **Assets**, click the file whose name starts with **extract_fanfic_metadata** to download it. Don't unzip it.
2. In Calibre, open **Preferences → Plugins → Load plugin from file** and choose the ZIP file you downloaded.
3. Calibre warns that plugins are a security risk. If you downloaded the file from the release page above, click **Yes**.

   ![Calibre asks “Are you sure?” about installing a plugin, with No and Yes buttons]({{ '/assets/img/install-warning.png' | relative_url }}){: .small}

4. Calibre asks where to put the button. Make sure **The main toolbar** is selected and click **OK**. This window uses the plugin’s old name, **Extract Epub Metadata**.

   ![A list of toolbars and menus, with the two main toolbar entries selected]({{ '/assets/img/install-toolbars.png' | relative_url }}){: .small}

5. Click **Restart calibre now**.

   ![The Success message, with Restart calibre now and OK buttons]({{ '/assets/img/install-success.png' | relative_url }}){: .small}

You now have an **Extract Metadata** button on the toolbar.

![Calibre’s main window with the Extract Metadata button highlighted at the right of the toolbar]({{ '/assets/img/toolbar-button.png' | relative_url }})

## 2. Choose what to update {#settings}

Open **Preferences → Plugins → Extract Fanfic Metadata → Customize plugin**.

For your first go:

- Tick **Update standard Calibre metadata**. This fills Calibre's own fields, such as author, tags and summary.
- Untick **Save all extracted metadata**. It's on to begin with, but it's meant for [use with FanFicFare](#fanficfare) and needs a column set up first.
- Leave **Preview before writing** ticked.

![The plugin’s settings with only Update standard Calibre metadata ticked among the three choices]({{ '/assets/img/settings-first-run.png' | relative_url }}){: .small}

<div class="callout note">
  <div class="callout-title">Your existing details are safe</div>
  <p>Anything already filled in is kept, including the title. Only empty fields, and an author listed as “Unknown”, are filled. If you <em>want</em> to replace what's there, such as a title that is really a file name, tick <strong>Overwrite existing standard metadata</strong>.</p>
</div>

## 3. Try it on a few books {#first-run}

<div class="callout warning">
  <div class="callout-title">Back up first</div>
  <p>Back up your library before changing lots of books at once. Start with two or three.</p>
</div>

1. Select the books.
2. Click **Extract Metadata** on the toolbar.
3. A preview lists your books. Click each one to see what was found, and what will be skipped because it's already filled in.

   ![The preview window, listing three books, with the date, series and tags to be added to the first and the details it already has]({{ '/assets/img/preview-window.png' | relative_url }})

   In this example the title, author, summary and language were already there, so they’re kept. The date, series, tags and story link will be added.

4. Untick any book you want to leave alone.
5. Click **Write Selected**. A short message tells you how many books were updated.

Nothing is changed until you click **Write Selected**. Afterwards, the new details are in your library:

![The library after writing, with tags and a series filled in and the tags listed beside the selected book]({{ '/assets/img/library-after.png' | relative_url }})

## Fill your own columns {#columns}

If you have your own columns in Calibre, such as one for word count or fandom, the plugin can fill them.

1. If you don’t have the column yet, create it under **Preferences → Add your own columns**. Give it a lookup name (such as `words`), a heading (such as **Words**) and a type. For a word count, choose **Integers**. For fandom, choose **Comma separated text, like tags**. Then restart Calibre.

   ![The Create a custom column window, set up for a Words column of type Integers]({{ '/assets/img/create-column.png' | relative_url }}){: .small}

2. In the plugin’s settings, tick **Update custom columns**.
3. Click **Configure column mapping…**.
4. Next to each detail you want, such as **Word Count**, pick your column.
5. Tick **Overwrite** only for columns you want replaced every time. Unticked columns are only filled when empty.

   ![The column mapping window, with Fandom(s) set to the Fandom column and Word Count set to the Words column]({{ '/assets/img/column-mapping.png' | relative_url }})

6. Click **OK** to close both windows, then select your books, click **Extract Metadata** and **Write Selected**.

   ![The book list with the new Fandom and Words columns filled in]({{ '/assets/img/columns-filled.png' | relative_url }})

The [full list of details you can use](https://github.com/wordsandpics/Extract-fanfic-metadata/blob/main/SETTINGS.md#fields) is on GitHub.

## Use it with FanFicFare {#fanficfare}

If you've set up FanFicFare to tidy tags and fill columns your way, let it do that for these books too.

1. You need a **Long text** column for FanFicFare's Saved Metadata. FanFicFare's own **Saved Metadata Column** setting must point to it.
2. In this plugin's settings, tick **Save all extracted metadata** and choose the same column.
3. Select your books and run **Extract Metadata**.
4. Then run FanFicFare's **Update Calibre Metadata from Saved Metadata Column**.

This only works for books where a story link that FanFicFare supports was found. The preview tells you when one is skipped.

## Something not working? {#help}

**A field didn't change.** It probably already had something in it. The preview lists these. Tick **Overwrite** if you want it replaced.

**Some details are missing.** The plugin only uses what's inside the file, and leaves the rest blank. It never guesses.

**The book isn't recognised.** Not every layout can be read. Scanned PDFs and pages printed to PDF from a browser don't work.

**It's a web page you saved yourself.** Convert it to EPUB in Calibre first, then run the plugin.

**“Choose a Long Text Saved Metadata column”.** Untick **Save all extracted metadata** in the settings, or [set up the column](#fanficfare).

**Word count or status looks out of date.** They describe your saved copy, not the story online today.

Still stuck? [Open an issue on GitHub](https://github.com/wordsandpics/Extract-fanfic-metadata/issues). It's looked after in spare time, so replies may be slow.

## More

- [Every setting and field](https://github.com/wordsandpics/Extract-fanfic-metadata/blob/main/SETTINGS.md), including anthologies
- [What's changed](https://github.com/wordsandpics/Extract-fanfic-metadata/blob/main/CHANGELOG.md)

The plugin is provided as it is, with limited support. This guide isn't affiliated with AO3 or the Organization for Transformative Works.
