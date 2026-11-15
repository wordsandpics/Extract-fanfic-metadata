"""AO3 HTML downloads, as Calibre stores them.

When an .html file is added, Calibre's "HTML to ZIP" step normally stores it
as a ZIP book holding the page (and any images); with that step turned off it
stays an HTML book. Either way the page is AO3's ordinary download: the same
preface (Rating/Archive Warning/... list, title, byline, Summary) that AO3
puts at the front of its EPUBs, but as HTML rather than XHTML.

This module tidies the opening of that page into well-formed XHTML with the
standard library's tolerant HTMLParser and wraps it in a minimal in-memory
EPUB, so the existing EPUB readers run unchanged. The user's file is never
modified. Only the preface is read: the page is cut at AO3's chapters block.
"""
import io
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from zipfile import BadZipFile, ZipFile, ZIP_DEFLATED

# Only the opening is needed; AO3's preface ends where the chapters begin.
MAX_HTML_BYTES = 2 * 1024 * 1024
_CHAPTERS_RE = re.compile(rb'<div[^>]*\bid=["\']chapters["\']', re.I)
# AO3's download preface: "Posted originally on the Archive of Our Own at <work link>".
# Browser-saved work pages lack it and are left to the EPUB conversion route.
_AO3_PREFACE_RE = re.compile(rb'Posted originally on the.{0,400}?archiveofourown\.org/works/\d+', re.I | re.S)

_VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
         'meta', 'param', 'source', 'track', 'wbr'}
_SKIP = {'script', 'style', 'noscript', 'template'}
# Opening one of these closes an open <p>, as browsers do.
_CLOSES_P = {'address', 'article', 'aside', 'blockquote', 'div', 'dl', 'fieldset',
             'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hr',
             'ol', 'p', 'pre', 'section', 'table', 'ul'}
_SIBLINGS = {'li': {'li'}, 'dt': {'dt', 'dd'}, 'dd': {'dt', 'dd'},
             'tr': {'tr'}, 'td': {'td', 'th'}, 'th': {'td', 'th'}, 'option': {'option'}}
_ATTR_RE = re.compile(r'^[A-Za-z_][\w.\-]*$')


class _TreeBuilder(HTMLParser):
    """Forgiving HTML -> ElementTree; mismatched or missing end tags are repaired."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = ET.Element('root')
        self.stack = [self.root]
        self.skip = 0

    def _append(self, tag, attrs):
        elem = ET.SubElement(self.stack[-1], tag)
        for name, value in attrs:
            if _ATTR_RE.match(name or ''):
                elem.set(name.lower(), value or '')
        return elem

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self.skip or tag in _SKIP:
            if tag in _SKIP:
                self.skip += 1
            return
        if tag in _CLOSES_P:
            self._close_open('p', stop_at={'div', 'blockquote', 'li', 'dd', 'td', 'th'})
        if tag in _SIBLINGS:
            top = self.stack[-1].tag
            if top in _SIBLINGS[tag]:
                self.stack.pop()
        elem = self._append(tag, attrs)
        if tag not in _VOID:
            self.stack.append(elem)

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        if not self.skip and tag not in _SKIP:
            self._append(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in _SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip or tag in _VOID:
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return
        # A stray end tag with no matching start is ignored.

    def _close_open(self, tag, stop_at):
        for i in range(len(self.stack) - 1, 0, -1):
            current = self.stack[i].tag
            if current == tag:
                del self.stack[i:]
                return
            if current in stop_at:
                return

    def handle_data(self, data):
        if self.skip or not data:
            return
        parent = self.stack[-1]
        if len(parent):
            last = parent[-1]
            last.tail = (last.tail or '') + data
        else:
            parent.text = (parent.text or '') + data


def html_to_xhtml(data):
    """Bytes of a (possibly sloppy) HTML page -> well-formed XHTML bytes."""
    text = data.decode('utf-8', errors='replace')
    builder = _TreeBuilder()
    builder.feed(text)
    builder.close()
    html = next((e for e in builder.root if e.tag == 'html'), None)
    if html is None:
        html = ET.Element('html')
        html.extend(list(builder.root))
        if builder.root.text:
            html.text = builder.root.text
    html.set('xmlns', 'http://www.w3.org/1999/xhtml')
    return ET.tostring(html, encoding='utf-8')


def _opening(data):
    data = data[:MAX_HTML_BYTES]
    m = _CHAPTERS_RE.search(data)
    return data[:m.start()] if m else data


_CONTAINER = (b'<?xml version="1.0"?><container version="1.0" '
              b'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
              b'<rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>'
              b'</rootfiles></container>')
# No title or creator: the page's own preface supplies them. AO3's browser
# title ("Title - author - fandom") is deliberately not used.
_OPF = (b'<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" '
        b'version="2.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"></metadata>'
        b'<manifest><item id="page" href="page.xhtml" media-type="application/xhtml+xml"/>'
        b'</manifest><spine><itemref idref="page"/></spine></package>')


def _wrap_as_epub(xhtml):
    out = io.BytesIO()
    with ZipFile(out, 'w', ZIP_DEFLATED) as zf:
        zf.writestr('mimetype', 'application/epub+zip')
        zf.writestr('META-INF/container.xml', _CONTAINER)
        zf.writestr('content.opf', _OPF)
        zf.writestr('page.xhtml', xhtml)
    out.seek(0)
    return out


def _read_all(stream):
    if hasattr(stream, 'read'):
        return stream.read()
    with open(stream, 'rb') as f:
        return f.read()


def ao3_html_page(stream, is_zip):
    """The AO3 download page from a Calibre ZIP or HTML book, or None.

    For a ZIP, the HTML files at any depth are tried in name order; the first
    that names an AO3 work in its opening is used.
    """
    data = _read_all(stream)
    if not is_zip:
        return _opening(data) if _AO3_PREFACE_RE.search(_opening(data)) else None
    try:
        with ZipFile(io.BytesIO(data)) as zf:
            names = sorted(n for n in zf.namelist()
                           if n.lower().endswith(('.html', '.htm', '.xhtml')))
            for name in names:
                with zf.open(name) as f:
                    page = _opening(f.read(MAX_HTML_BYTES))
                if _AO3_PREFACE_RE.search(page):
                    return page
    except (BadZipFile, OSError):
        return None
    return None


def html_as_epub(stream, is_zip):
    """An in-memory EPUB holding the AO3 preface, or None when none is found."""
    page = ao3_html_page(stream, is_zip)
    if page is None:
        return None
    return _wrap_as_epub(html_to_xhtml(page))
