"""AO3 stories saved by ficdownloader (OPF generator "Ebook-lib").

Its intro.xhtml "About" page lists AO3 metadata as labelled paragraphs:

    <div class="metadata">
    <p><span class="metadata-label">Rating:</span> Mature</p>
    ...
    <p><span class="metadata-label">Source:</span> <a href="...">...</a></p>
    </div>
    <h2>Summary</h2>
    <p>...</p>
    <h2>Notes</h2>

Recognized by that metadata block, not by file name or generator. The tool
itself leaves some values out: a single fandom or relationship, the
"No Archive Warnings Apply" warning, and sometimes part or all of the
summary. Only what the page states is used; nothing is filled in.
"""
import re

from ._epubxml import find_all, find_first, local_name, parse_opf, parse_xhtml, spine_item_paths, text_content
from ._urls import canonical_ao3_url
from .ao3_frontmatter import _text_with_breaks, parse_series, series_fields

SOURCE = 'ficdownloader'

_LIST_LABELS = {
    'author': 'author',
    'warnings': 'warnings',
    'archive warning': 'warnings',
    'archive warnings': 'warnings',
    'fandom': 'fandoms',
    'fandoms': 'fandoms',
    'category': 'ao3categories',
    'categories': 'ao3categories',
    'characters': 'characters',
    'relationship': 'ships',
    'relationships': 'ships',
    'additional tags': 'freeformtags',
}
_SCALAR_LABELS = {
    'rating': 'rating',
    'language': 'language',
    'words': 'numWords',
    'published': 'datePublished',
    'updated': 'dateUpdated',
}
_CHAPTERS_RE = re.compile(r'^\s*(\d+)\s*/\s*(\d+|\?)\s*$')


def _split(value):
    return [p.strip() for p in re.split(r',\s*', value) if p.strip()]


def _metadata_block(root):
    for div in find_all(root, 'div'):
        if 'metadata' not in (div.get('class') or '').split():
            continue
        labels = [s for s in find_all(div, 'span')
                  if 'metadata-label' in (s.get('class') or '').split()]
        if len(labels) >= 2:
            return div
    return None


def _summary(root):
    """Paragraphs between the "Summary" heading and the next heading."""
    body = find_first(root, 'body')
    if body is None:
        return None
    paragraphs, inside = [], False
    for child in body:
        tag = local_name(child.tag)
        if tag in ('h1', 'h2', 'h3'):
            if inside:
                break
            inside = ' '.join(text_content(child).split()).lower() == 'summary'
            continue
        if inside:
            # A wrapper (blockquote, details...) contributes its own paragraphs.
            parts = [child] if tag == 'p' else list(find_all(child, 'p')) or [child]
            paragraphs.extend(t for t in map(_text_with_breaks, parts) if t)
    return '\n\n'.join(paragraphs) or None


def _read_block(block, result):
    for p in find_all(block, 'p'):
        span = next((s for s in find_all(p, 'span')
                     if 'metadata-label' in (s.get('class') or '').split()), None)
        if span is None:
            continue
        label = text_content(span).strip().rstrip(':').strip().lower()
        value = ' '.join(text_content(p).split())
        value = value.split(':', 1)[1].strip() if ':' in value else ''
        if label == 'source':
            link = next((a.get('href') for a in find_all(p, 'a') if a.get('href')), None) or value
            if link.startswith('http'):
                result['storyUrl'] = canonical_ao3_url(link.strip())
            continue
        if not value:
            continue
        if label in _LIST_LABELS:
            result[_LIST_LABELS[label]] = _split(value)
        elif label in _SCALAR_LABELS:
            result[_SCALAR_LABELS[label]] = value
        elif label == 'series':
            result.update(series_fields(parse_series([p])))
        elif label == 'chapters':
            m = _CHAPTERS_RE.match(value)
            if m:
                n, total = m.groups()
                result['numChapters'] = n
                result['chapterslashtotal'] = '%s/%s' % (n, total)
                if total != '?':
                    result['numChaptersTotal'] = total
                    result.setdefault('status', 'Completed' if n == total else 'In-Progress')
        elif label == 'status':
            result['status'] = 'Completed' if value.lower().startswith('complete') else 'In-Progress'


def extract_ficdownloader(zf):
    """Fields from a ficdownloader "About" page, or {} for other EPUBs."""
    opf_root, opf_path = parse_opf(zf)
    if opf_root is None:
        return {}
    for path in spine_item_paths(zf, opf_root, opf_path)[:4]:
        root = parse_xhtml(zf, path)
        block = _metadata_block(root) if root is not None else None
        if block is None:
            continue
        result = {}
        h1 = find_first(root, 'h1')
        if h1 is not None and text_content(h1).strip():
            result['title'] = ' '.join(text_content(h1).split())
        _read_block(block, result)
        summary = _summary(root)
        if summary:
            result['description'] = summary
        return result
    return {}
