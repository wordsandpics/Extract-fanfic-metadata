"""Collection facts from outer OPF, embedded stories, or a saved series page.

Never run the single-story cascade for a collection. In particular, its
series URL is not a storyUrl and its first story is not the whole book.
"""
import re
from urllib.parse import urlsplit

from .anthology import extract_fic_records, is_anthology, _parse_date
from .extractors._epubxml import (
    find_all, local_name, parse_opf, parse_xhtml, spine_item_paths, text_content,
)
from .extractors._numbers import parse_count
from .extractors._urls import canonical_ao3_url, unwrap_wayback_url
from .extractors.opf import extract_opf


def primary_url(opf):
    for scheme in ('url', 'uri'):
        candidate = (opf.get('identifiers') or {}).get(scheme)
        if candidate and candidate.startswith(('http://', 'https://')):
            return candidate
    return opf.get('dc_source')


def extract_collection(zf, opf=None):
    """Return (fields, sources) or None for an ordinary story EPUB."""
    opf = extract_opf(zf) if opf is None else opf
    raw_url = primary_url(opf)
    url = unwrap_wayback_url(raw_url) or raw_url
    url = canonical_ao3_url(url) or url
    merged = is_anthology(zf)
    series_url = bool(url and re.fullmatch(r'/series/[0-9]+/?', urlsplit(url).path))
    if not merged and not series_url:
        return None

    fields = {'collectionType': 'epubmerge anthology' if merged else 'series collection'}
    for old, new in (('title', 'title'), ('authors', 'author'),
                     ('language', 'langcode'), ('description', 'description'),
                     ('subjects', 'collectionTags')):
        if opf.get(old):
            fields[new] = opf[old]
    if url:
        fields['collectionUrl'] = url
    if unwrap_wayback_url(raw_url):
        fields['waybackUrl'] = raw_url
    sources = {k: 'collection_opf' for k in fields}

    if merged:
        records = extract_fic_records(zf)
        fields['collectionRecords'] = records
        if records:
            fields['collectionStoryCount'] = len(records)
            fields['collectionUnknownCount'] = sum(
                r.get('status') not in ('Completed', 'In-Progress') for r in records)
            if fields['collectionUnknownCount'] < len(records):
                fields['collectionCompletedCount'] = sum(r.get('status') == 'Completed' for r in records)
            # A lost/unreadable title page must not yield a partial total
            # presented as if it covered every original book in the merge.
            root, _ = parse_opf(zf)
            originals = sum(e.get('media-type') == 'origrootfile/xml'
                            for e in find_all(root, 'item')) if root is not None else 0
            if not originals or originals == len(records):
                for key, total in (('numWords', 'numWords'),
                                   ('numChapters', 'collectionChapterCount')):
                    values = [parse_count(r.get(key)) for r in records]
                    if all(v is not None for v in values):
                        fields[total] = sum(values)
            fields.update(_combined_story_fields(records))
            sources.update({k: 'collection_stories' for k in fields if k not in sources})
        series_status = _series_status(opf)
        if series_status:
            fields['collectionSeriesStatus'] = series_status
            sources['collectionSeriesStatus'] = 'collection_opf'
    else:
        reported = _series_page_fields(zf)
        fields.update(reported)
        sources.update({k: 'collection_series_page' for k in reported})
    return fields, sources


def _combined_story_fields(records):
    """Anthology-wide values built the way FanFicFare builds its own
    anthology metadata: lists joined without duplicates (first appearance
    order), earliest published date, latest updated date."""
    combined = {}
    for key, out in (('fandoms', 'collectionFandoms'), ('characters', 'collectionCharacters'),
                     ('ships', 'collectionShips')):
        values = list(dict.fromkeys(v for r in records for v in r.get(key) or []))
        if values:
            combined[out] = values
    published = [r['datePublished'] for r in records if r.get('datePublished')]
    if published:
        combined['collectionEarliestPublished'] = min(published)
    updated = [r['dateUpdated'] for r in records if r.get('dateUpdated')]
    if updated:
        combined['collectionLatestUpdated'] = max(updated)
    return combined


def _series_status(opf):
    """FanFicFare drops the stories' own Completed/In-Progress tags when it
    merges an anthology, then adds the series page's status (when the site
    gives one). So a single status tag on the outer book is the series status."""
    found = {s for s in (opf.get('subjects') or []) if s in ('Completed', 'In-Progress')}
    return found.pop() if len(found) == 1 else None


def _series_page_fields(zf):
    root, path = parse_opf(zf)
    if root is None:
        return {}
    for item in spine_item_paths(zf, root, path):
        page = parse_xhtml(zf, item)
        if page is None:
            continue
        for dl in find_all(page, 'dl'):
            pairs = {}
            label = None
            for child in dl:
                if local_name(child.tag) == 'dt':
                    label = text_content(child).strip().rstrip(':').lower()
                elif local_name(child.tag) == 'dd' and label:
                    pairs[label] = text_content(child).strip()
                    label = None
            if 'works' not in pairs or 'complete' not in pairs:
                continue
            result = {}
            for label, key in (('works', 'collectionStoryCount'), ('words', 'numWords')):
                n = parse_count(pairs.get(label))
                if n is not None:
                    result[key] = n
            if pairs['complete'].lower() in ('yes', 'no'):
                result['collectionStatus'] = ('Completed' if pairs['complete'].lower() == 'yes'
                                              else 'In-Progress')
            # These are series dates, not the dates of the first work.
            for outer in find_all(page, 'dl'):
                current = None
                for child in outer:
                    if local_name(child.tag) == 'dt':
                        current = text_content(child).strip().rstrip(':').lower()
                    elif local_name(child.tag) == 'dd':
                        key = {'series begun': 'collectionDateBegun',
                               'series updated': 'collectionDateUpdated'}.get(current)
                        date = _parse_date(text_content(child).strip()) if key else None
                        if date is not None:
                            result[key] = date
                        current = None
            return result
    return {}
