#!/usr/bin/env python3
"""Build the Low Republic wiki.

Reads the articles in ARTICLES/ and the images in ARTWORKS/, and writes a static
website to WIKI-SITE/_site/. It never writes to ARTICLES/ or ARTWORKS/.

    python WIKI-SITE/build.py              build the site
    python WIKI-SITE/build.py --strict     also fail if anything is unresolved
    python -m http.server -d WIKI-SITE/_site    preview it at http://localhost:8000

The article format is specified in ARTICLES/_FORMAT.md. The design of the site
is in WIKI-SITE/GAMEPLAN.md.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.parse
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ARTICLES = ROOT / "ARTICLES"
ARTWORKS = ROOT / "ARTWORKS"
LOGOS = {
    "logo-wide.png": ROOT / "lowrepubliclogowide.png",
    "logo-tall.png": ROOT / "lowrepubliclogotall.png",
}

# category -> folder, in the order the format lists them
FOLDERS = {
    "history": "history",
    "faction": "factions",
    "character": "characters",
    "place": "places",
    "page": "pages",
}
MAIN_PAGE = "Main Page"
IMAGE_KEYS = ("image", "image_caption", "artwork_author", "artwork_author_link")
# Tag vocabularies of _FORMAT 3.4, in display order, for the category filters.
PERIODS = ["Before 19 BBY", "Long War", "15 BBY–0 ABY", "Shadow War"]
REGIONS = ["Core", "Inner Rim", "Mid Rim", "Outer Rim", "Hutt Space", "Wild Space"]
WEB_WIDTHS = (300, 600)  # web copies of each raster image: 1x and 2x for a ~300px box
LARGE_SIDE = 1600  # the copy shown when an image is clicked: longest side, in pixels
MAP_WIDTHS = (960, 1920)  # web copies of the Main Page map: 1x and 2x for the full-width box
FFMPEG = shutil.which("ffmpeg")  # optional: faster-starting video and its still image
PAGE_BACKGROUND = "#0f0f10"  # matches --bg in style.css

WIKILINK_RE = re.compile(r"\[\[([^\[\]|#]+)(?:#([^\[\]|]+))?(?:\\?\|([^\[\]]+))?\]\]")
HATNOTE_RE = re.compile(r"^\*((?:Main articles?|See also|Further information): .+)\*$")
HEADING_RE = re.compile(r"^(#{2,3}) (.+)$")
FENCE_RE = re.compile(r"^```\s*(\w*)\s*$")


class BuildError(Exception):
    """A problem that stops the build, such as front matter that will not parse."""


# --------------------------------------------------------------------------
# Names, slugs and anchors
# --------------------------------------------------------------------------


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def title_slug(title: str) -> str:
    """The file-name rule of _FORMAT 1: lowercase, no accents, no apostrophes or
    full stops, spaces become hyphens."""
    text = strip_accents(title).lower().replace("'", "").replace("’", "").replace(".", "")
    return text.replace(" ", "-")


def url_slug(name: str) -> str:
    """A URL-safe slug for redirect names, which may hold any punctuation."""
    text = re.sub(r"[^a-z0-9-]+", "-", title_slug(name))
    return re.sub(r"-{2,}", "-", text).strip("-")


def anchor(heading: str) -> str:
    """The anchor of a heading: `The schism, 14–8 BBY` -> `the-schism-14-8-bby`."""
    text = strip_accents(heading).lower().replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "section"


def unique_anchors(texts):
    """Anchors for a list of headings, numbering any repeats (`-2`, `-3`)."""
    seen: dict[str, int] = {}
    out = []
    for text in texts:
        base = anchor(text)
        seen[base] = seen.get(base, 0) + 1
        out.append(base if seen[base] == 1 else f"{base}-{seen[base]}")
    return out


def svg_size(path: Path) -> tuple[int | None, int | None]:
    """The width and height of an SVG, from its width/height attributes or its viewBox."""
    head = path.read_text(encoding="utf-8", errors="ignore")[:8000]
    tag = re.search(r"<svg\b[^>]*>", head, re.S)
    if not tag:
        return None, None
    tag = tag.group(0)

    def number(attr):
        m = re.search(rf'(?<![\w-]){attr}\s*=\s*["\']\s*([\d.]+)\s*(?:px)?\s*["\']', tag)
        return float(m.group(1)) if m else None

    width, height = number("width"), number("height")
    if not (width and height):
        m = re.search(r'viewBox\s*=\s*["\']([^"\']+)["\']', tag)
        parts = re.split(r"[\s,]+", m.group(1).strip()) if m else []
        if len(parts) == 4:
            width, height = float(parts[2]), float(parts[3])
    return (round(width), round(height)) if width and height else (None, None)


def search_text(fragment: str) -> str:
    """Plain text for the search index. Images and their credits are left out; inline tags
    vanish ("<a>Dathomir</a>." stays "Dathomir."), block tags become spaces."""
    fragment = re.sub(r"<figure\b.*?</figure>", " ", fragment, flags=re.S)
    fragment = re.sub(r"<h[1-6]\b.*?</h[1-6]>", " ", fragment, flags=re.S)  # headings are indexed apart
    fragment = re.sub(r'<div class="hatnote".*?</div>', " ", fragment, flags=re.S)  # "Main article:" pointers
    fragment = re.sub(r"</?(?:a|strong|em|b|i|span|mark|sup|sub|code)\b[^>]*>", "", fragment)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def plain_text(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def first_sentence(text: str, limit: int = 240) -> str:
    """The lead's first sentence, for category listings."""
    text = " ".join(text.split())
    m = re.match(r"(.{30,}?[.!?])(?:\s+(?=[A-Z\"'‘“])|$)", text)
    sentence = m.group(1) if m else text
    return sentence if len(sentence) <= limit else sentence[:limit].rsplit(" ", 1)[0] + "…"


def sort_key(art) -> str:
    """Alphabetical order that ignores a leading "The", as an index would."""
    title = re.sub(r"^The\s+", "", art.title)
    return strip_accents(title).casefold()


def first_sentences(text: str, limit: int = 220) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text.rfind(". ", 0, limit)
    return text[: cut + 1] if cut > 60 else text[:limit].rsplit(" ", 1)[0] + "…"


# --------------------------------------------------------------------------
# Reading articles
# --------------------------------------------------------------------------


@dataclass
class Article:
    path: Path
    meta: dict
    body: str
    slug: str
    headings: list = field(default_factory=list)  # (level, text, anchor)
    anchors: dict = field(default_factory=dict)  # heading text -> anchor
    excerpt: str = ""  # the lead's first sentence, filled in when the page is rendered
    text: str = ""  # the infobox and body as plain text, for the search index

    @property
    def title(self) -> str:
        return self.meta["title"]

    @property
    def category(self) -> str:
        return self.meta["category"]

    @property
    def infobox(self) -> dict | None:
        return self.meta.get("infobox")

    @property
    def url(self) -> str:
        """The page's path relative to the site root."""
        return "" if self.title == MAIN_PAGE else f"wiki/{self.slug}/"

    @property
    def root(self) -> str:
        """The relative path from this page back to the site root."""
        return "" if self.title == MAIN_PAGE else "../../"


def normalise(raw: str) -> str:
    """UTF-8 text with Windows line endings and trailing spaces removed."""
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in raw.split("\n"))


def fenced_lines(lines) -> set[int]:
    """Indices of lines that are inside (or are the fences of) a ``` block."""
    inside, out = False, set()
    for i, line in enumerate(lines):
        if line.startswith("```"):
            out.add(i)
            inside = not inside
        elif inside:
            out.add(i)
    return out


def read_article(path: Path) -> Article:
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    raw = normalise(path.read_bytes().decode("utf-8-sig"))
    if not raw.startswith("---\n"):
        raise BuildError(f"{rel}: the file does not start with front matter (---)")
    end = raw.find("\n---\n", 3)
    if end < 0:
        raise BuildError(f"{rel}: the front matter is never closed with ---")
    try:
        meta = yaml.safe_load(raw[4:end]) or {}
    except yaml.YAMLError as exc:
        raise BuildError(f"{rel}: the front matter is not valid YAML\n{exc}") from exc
    for key in ("title", "category"):
        if not meta.get(key):
            raise BuildError(f"{rel}: front matter has no `{key}`")
    meta["title"] = str(meta["title"])
    art = Article(path=path, meta=meta, body=raw[end + 5 :], slug=path.stem)

    lines = art.body.split("\n")
    fenced = fenced_lines(lines)
    found = [(len(m.group(1)), m.group(2)) for i, line in enumerate(lines)
             if i not in fenced and (m := HEADING_RE.match(line))]
    for (level, text), anc in zip(found, unique_anchors(t for _, t in found)):
        art.headings.append((level, text, anc))
        art.anchors.setdefault(text, anc)
    return art


# --------------------------------------------------------------------------
# The site
# --------------------------------------------------------------------------


class Site:
    def __init__(self, config: dict, out: Path):
        self.config = config
        self.out = out
        self.articles: dict[str, Article] = {}
        self.redirects: dict[str, tuple[Article, str | None, str]] = {}  # url slug -> (target, heading, name)
        self.warnings: list[str] = []
        self.media: dict[str, dict | None] = {}
        self.media_written: set[Path] = set()
        self.hidden = set(config.get("hidden") or [])
        # hidden articles may still appear on their own category page (config `hidden_on_category_pages`)
        self.hidden_on_category_pages = bool(config.get("hidden_on_category_pages"))
        self.quarantine = set(config.get("quarantine") or [])
        # the masterdoc as one page; `sources` codes point into it (config `history_page`)
        self.history_page = str(config.get("history_page") or "The Entire History")
        self.sections: dict[str, dict] = {}  # source code ("X.4", "XV", "Pref") -> heading on that page
        self.credits: dict[str, dict] = {}  # artist -> {"link", "articles": {title: count}}
        self.md = self._make_markdown()
        self.jinja = Environment(
            loader=FileSystemLoader(HERE / "templates"),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")

    # ---- loading ----------------------------------------------------------

    def load(self) -> None:
        for category, folder in FOLDERS.items():
            for path in sorted((ARTICLES / folder).glob("*.md")):
                if path.name.startswith("_"):
                    continue
                art = read_article(path)
                rel = path.relative_to(ROOT)
                if art.category != category:
                    self.warn(str(rel), f"category `{art.category}` does not match the folder {folder}/")
                if title_slug(art.title) != art.slug:
                    self.warn(str(rel), f"the title slugs to {title_slug(art.title)}.md")
                if art.title in self.articles:
                    raise BuildError(f"{rel}: the title `{art.title}` is already used by "
                                     f"{self.articles[art.title].path.relative_to(ROOT)}")
                self.articles[art.title] = art
        if MAIN_PAGE not in self.articles:
            raise BuildError(f"there is no article titled `{MAIN_PAGE}`")
        for name in self.hidden | self.quarantine:
            if name not in self.articles:
                self.warn("config.yml", f"`{name}` is not an article title")

        slugs = {a.slug for a in self.articles.values()}
        for art in self.articles.values():
            for entry in art.meta.get("redirects") or []:
                name, _, heading = str(entry).partition("#")
                name, heading = name.strip(), heading.strip() or None
                slug = url_slug(name)
                where = f"{art.title} (redirect `{entry}`)"
                if heading and heading not in art.anchors:
                    self.warn(where, f"there is no heading `{heading}`; it will lead to the top")
                    heading = None
                if slug == art.slug and not heading:
                    continue  # the name already leads here: /wiki/<slug>/ is this article
                if not slug or slug in slugs:
                    self.warn(where, f"the address /wiki/{slug}/ is taken by an article; skipped")
                elif slug in self.redirects and self.redirects[slug][0] is not art:
                    self.warn(where, f"/wiki/{slug}/ already leads to {self.redirects[slug][0].title}; skipped")
                else:
                    self.redirects[slug] = (art, heading, name)
        self._index_history()

    def _index_history(self) -> None:
        """Map source codes to the history page's headings: `Pref` is the preface, `XI` a whole
        chapter (`## XI. ...`), `XI.2` the second `###` under it (_FORMAT 3.3, handoff brief)."""
        hist = self.articles.get(self.history_page)
        if hist is None:
            self.warn("config.yml", f"there is no `{self.history_page}` page (history_page), so no \"In the history\" boxes")
            return
        chapter, count = None, 0
        for order, (level, text, anc) in enumerate(hist.headings):
            if level == 2:
                m = re.match(r"^([IVXLC]+)\.\s+(.+)$", text)
                chapter, count = (m.group(1), 0) if m else (None, 0)
                if m:
                    self.sections[chapter] = {"anchor": anc, "title": m.group(2), "order": order}
                elif text == "Preface":
                    self.sections["Pref"] = {"anchor": anc, "title": "Preface", "order": order}
            elif level == 3 and chapter:
                count += 1
                self.sections[f"{chapter}.{count}"] = {"anchor": anc, "title": text, "order": order}
        for art in self.articles.values():
            for code in art.meta.get("sources") or []:
                code = str(code).strip()
                if code.startswith("R:"):
                    if code[2:].strip() not in self.articles:
                        self.warn(art.title, f"source `{code}`: no article has that title")
                elif code not in self.sections:
                    self.warn(art.title, f"source `{code}` matches no heading on {self.history_page}")

    # ---- links --------------------------------------------------------------

    def link(self, target: str, heading: str | None, env: dict) -> tuple[str, bool]:
        """The href for a wiki-link, relative to the page being rendered."""
        art = self.articles.get(target)
        if art is None:
            self.warn(env["where"], f"[[{target}]] does not match any article title")
            return "#", False
        href = env["root"] + art.url or "./"
        if heading:
            anc = art.anchors.get(heading)
            if anc is None:
                self.warn(env["where"], f"[[{target}#{heading}]]: {target} has no such heading")
            else:
                href += "#" + anc
        env.setdefault("links", []).append(target)
        return href, True

    def _make_markdown(self) -> MarkdownIt:
        md = MarkdownIt("commonmark", {"html": True}).enable("table")
        site = self

        def wikilink(state, silent):
            if not state.src.startswith("[[", state.pos):
                return False
            m = WIKILINK_RE.match(state.src, state.pos)
            if not m:
                return False
            if not silent:
                target, heading, text = (g.strip() if g else None for g in m.groups())
                href, ok = site.link(target, heading, state.env)
                token = state.push("link_open", "a", 1)
                token.attrSet("href", href)
                if not ok:
                    token.attrSet("class", "redlink")
                    token.attrSet("title", f"{target} (no such article)")
                state.push("text", "", 0).content = text or (f"{target} § {heading}" if heading else target)
                state.push("link_close", "a", -1)
            state.pos = m.end()
            return True

        def heading_ids(state):
            heads = [(i, state.tokens[i + 1].content) for i, t in enumerate(state.tokens)
                     if t.type == "heading_open"]
            for (i, text), anc in zip(heads, unique_anchors(t for _, t in heads)):
                state.tokens[i].attrSet("id", anc)

        md.inline.ruler.before("link", "wikilink", wikilink)
        md.core.ruler.push("heading_ids", heading_ids)
        return md

    def inline(self, text: str, env: dict) -> str:
        return self.md.renderInline(str(text), env)

    # ---- images -------------------------------------------------------------

    def image(self, name: str, where: str) -> dict | None:
        """Web copies of an ARTWORKS/ file: {src, srcset, width, height, original},
        all relative to the site root. SVGs are used as they are."""
        if name in self.media:
            return self.media[name]
        src = ARTWORKS / name
        if not src.is_file():
            self.warn(where, f"image `{name}` is not in ARTWORKS/")
            self.media[name] = None
            return None
        media = self.out / "media"
        original = media / "original" / name
        self._copy(src, original)
        info = {"original": f"media/original/{name}", "src": f"media/original/{name}",
                "srcset": None, "width": None, "height": None,
                "large": f"media/original/{name}", "large_w": None, "large_h": None}
        if src.suffix.lower() == ".svg":
            info["large_w"], info["large_h"] = svg_size(src)
        else:
            with Image.open(src) as im:
                im = ImageOps.exif_transpose(im)
                width, height = im.size
                alpha = im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info
                scale = min(1.0, LARGE_SIDE / max(width, height))
                sizes = [(f"{target}", min(target, width)) for target in WEB_WIDTHS]
                sizes.append(("large", round(width * scale)))
                made = {}
                for label, w in sizes:
                    h = round(height * w / width)
                    dest = media / f"{src.stem}-{label}.webp"
                    if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        copy = im.convert("RGBA" if alpha else "RGB").resize((w, h), Image.LANCZOS)
                        copy.save(dest, "WEBP", quality=84 if label == "large" else 82, method=4)
                    self.media_written.add(dest)
                    made[label] = (f"media/{dest.name}", w, h)
            info.update(src=made[str(WEB_WIDTHS[0])][0],
                        srcset=[made[str(t)][0] for t in WEB_WIDTHS],
                        width=WEB_WIDTHS[0], height=round(height * WEB_WIDTHS[0] / width),
                        large=made["large"][0], large_w=made["large"][1], large_h=made["large"][2],
                        original_w=width, original_h=height)
        self.media[name] = info
        return info

    def _copy(self, src: Path, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime or dest.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dest)
        self.media_written.add(dest)

    def image_box(self, data: dict, env: dict, alt: str, css: str) -> str:
        """The image part of an infobox or a figure: picture, optional caption,
        and the "Artwork by" credit (_FORMAT 4 and 5.6)."""
        info = self.image(str(data.get("image") or ""), env["where"])
        if info is None:
            return ""
        caption = str(data.get("image_caption") or "").strip()
        author = str(data.get("artwork_author") or "").strip()
        link = str(data.get("artwork_author_link") or "").strip()
        if not author:
            if str(data.get("image")) in (self.config.get("unknown_artist_images") or []):
                author = str(self.config.get("unknown_artist_label") or "")
            else:
                author = str(self.config.get("default_artwork_author") or "")  # official art, as a rule
        art = env.get("article")
        if author and author != self.config.get("unknown_artist_label") and art and art.title not in self.hidden:
            credit = self.credits.setdefault(author, {"link": "", "articles": {}})
            credit["articles"][art.title] = credit["articles"].get(art.title, 0) + 1
            credit["link"] = credit["link"] or link
        return self.jinja.get_template("_image.html").render(
            root=env["root"], info=info, css=css,
            alt=plain_text(self.inline(caption, env)) if caption else alt,
            caption=self.inline(caption, env) if caption else "",
            author=author, link=link,
        )

    # ---- rendering an article -------------------------------------------------

    def render_body(self, art: Article, env: dict) -> str:
        """The article body as HTML: image blocks moved to the top of the section
        they close, hatnotes marked, then the Markdown rendered."""
        lines = art.body.split("\n")
        fenced = fenced_lines(lines)
        headings = [i for i, line in enumerate(lines) if i not in fenced and HEADING_RE.match(line)]

        insert_at: dict[int, list[str]] = defaultdict(list)
        drop: set[int] = set()
        i = 0
        while i < len(lines):
            m = FENCE_RE.match(lines[i]) if i in fenced else None
            if not m:
                i += 1
                continue
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            if m.group(1) == "image":
                try:
                    data = yaml.safe_load("\n".join(lines[i + 1 : j])) or {}
                except yaml.YAMLError as exc:
                    self.warn(art.title, f"an image block is not valid YAML: {exc}")
                    data = {}
                drop.update(range(i, j + 1))
                before = [h for h in headings if h < i]
                if before:  # D3: to the top of the section it closes, after any hatnote
                    point = before[-1] + 1
                    k = point
                    while k < len(lines) and not lines[k]:
                        k += 1
                    if k < len(lines) and HATNOTE_RE.match(lines[k]):
                        point = k + 1
                else:
                    point = i
                figure = self.image_box(data, env, f"Artwork from {art.title}", "figure")
                if figure:
                    # one line: an HTML block in Markdown ends at the first blank line
                    insert_at[point].append(" ".join(ln.strip() for ln in figure.splitlines() if ln.strip()))
            i = j + 1

        out: list[str] = []
        for k in range(len(lines) + 1):
            for figure in insert_at.get(k, []):
                out += ["", figure, ""]
            if k == len(lines) or k in drop:
                continue
            line = lines[k]
            m = HATNOTE_RE.match(line) if k not in fenced else None
            if m:
                line = f'<div class="hatnote" role="note">{self.inline(m.group(1), env)}</div>'
            out.append(line)

        body = self.md.render("\n".join(out), env)
        if art.meta.get("canon") and "Background" in art.anchors:
            target, _, heading = self.config["canon_link"].partition("#")
            href, _ = self.link(target, heading or None, env)
            anc = art.anchors["Background"]
            body = body.replace(
                f'<h2 id="{anc}">Background</h2>',
                f'<h2 id="{anc}">Background <a class="tag" href="{href}" '
                f'title="This section summarises the original Star Wars canon">Canon</a></h2>', 1)
        return body

    def render_infobox(self, art: Article, env: dict) -> str:
        box = art.infobox
        if not box:
            return ""
        labels = self.config.get("labels") or {}
        rows = []
        for key, value in box.items():
            if key in IMAGE_KEYS or value in (None, "", []):
                continue
            if key == "name" and str(value) == art.title:
                continue  # the title band already says it
            items = [self.inline(v, env) for v in (value if isinstance(value, list) else [value])
                     if str(v).strip()]
            if not items:
                continue
            label = labels.get(key, key.replace("_", " ").capitalize())
            if isinstance(label, list):
                label = label[1] if len(items) > 1 and len(label) > 1 else label[0]
            rows.append((label, items))
        image = self.image_box(box, env, f"Artwork of {art.title}", "infobox-image") if box.get("image") else ""
        return self.jinja.get_template("_infobox.html").render(title=art.title, image=image, rows=rows)

    def history_box(self, art: Article, env: dict) -> str:
        """The "In the history" box (handoff brief): the passages of the history page that the
        article draws on, in the history's order, and the register entries it uses."""
        hist = self.articles.get(self.history_page)
        if art.category == "page" or hist is None:
            return ""
        passages, register, seen = [], [], set()
        for code in art.meta.get("sources") or []:
            code = str(code).strip()
            if code in seen:
                continue
            seen.add(code)
            if code.startswith("R:"):
                title = code[2:].strip()
                target = self.articles.get(title)
                linkable = (target is not None and target is not art and title not in self.hidden
                            and not (art.title in self.quarantine and title in self.quarantine))
                href = self.link(title, None, env)[0] if linkable else None
                register.append({"title": title, "href": href, "self": target is art})
            elif code in self.sections:
                sec = self.sections[code]
                passages.append({"code": "" if code == "Pref" else code, "title": sec["title"],
                                 "href": f"{env['root']}{hist.url}#{sec['anchor']}", "order": sec["order"]})
        if not passages and not register:
            return ""
        passages.sort(key=lambda p: p["order"])
        return self.jinja.get_template("_history_box.html").render(
            passages=passages, register=register, history_href=env["root"] + hist.url, history_title=hist.title)

    def chain_nav(self, art: Article, env: dict) -> str:
        """Previous and next links for history articles, from preceded_by and followed_by
        (_FORMAT 4.3.1). Where the chain branches, every branch is listed."""
        box = art.infobox or {}
        if art.category != "history" or not (box.get("preceded_by") or box.get("followed_by")):
            return ""

        def items(key):
            value = box.get(key) or []
            return [self.inline(v, env) for v in (value if isinstance(value, list) else [value])]

        return self.jinja.get_template("_chain_nav.html").render(
            previous=items("preceded_by"), following=items("followed_by"))

    def toc(self, art: Article) -> list[dict]:
        entries: list[dict] = []
        for level, text, anc in art.headings:
            if level == 2 or not entries:
                entries.append({"text": text, "anchor": anc, "children": []})
            else:
                entries[-1]["children"].append({"text": text, "anchor": anc})
        return entries

    def site_url(self) -> str:
        url = str(self.config.get("site_url") or "")
        return url if not url or url.endswith("/") else url + "/"

    def share_card(self) -> dict | None:
        """The default link-preview picture (config `social_image`), copied into media/."""
        if hasattr(self, "_card"):
            return self._card
        self._card = None
        name = self.config.get("social_image")
        src = ROOT / str(name or "")
        if name and not src.is_file():
            self.warn("config.yml", f"social_image `{name}` is not in the repository")
        elif name:
            dest = self.out / "media" / "social" / src.name
            self._copy(src, dest)
            with Image.open(src) as im:
                w, h = im.size
            self._card = {"url": self.site_url() + f"media/social/{src.name}", "width": w, "height": h,
                          "alt": self.config["site_name"]}
        return self._card

    def meta(self, path: str | None, art: Article | None = None) -> dict:
        """Values for the link-preview tags (Open Graph): the page's full address, and its
        picture: the article's own artwork when it has a photo-like image, else the card."""
        share = None
        box = (art.infobox or {}) if art else {}
        if box.get("image") and self.site_url():
            info = self.image(str(box["image"]), art.title)
            if info and info.get("original_w"):
                share = {"url": self.site_url() + info["original"], "width": info["original_w"],
                         "height": info["original_h"], "alt": f"Artwork of {art.title}"}
        if share is None and self.site_url():
            share = self.share_card()
        page_url = self.site_url() + path if (path is not None and self.site_url()) else ""
        return {"page_url": page_url, "share": share}

    def chrome(self, root: str) -> dict:
        """Template values shared by every page: sidebar links and categories."""
        nav = []
        for title in self.config.get("sidebar_links") or []:
            art = self.articles.get(title)
            if art:
                nav.append({"title": title, "href": root + art.url or "./"})
        cats = [{"label": c["label"], "href": f"{root}category/{FOLDERS[key]}/"}
                for key, c in (self.config.get("categories") or {}).items()]
        notice = self.config.get("disclaimer") or {}
        env = {"root": root, "where": "config.yml (disclaimer)", "links": []}
        disclaimer = notice and {
            "version": str(notice.get("version", 1)),
            "title": notice.get("title", ""),
            "paragraphs": [self.inline(p, env) for p in notice.get("paragraphs") or []],
            "button": notice.get("button") or "Acknowledge",
            "show_on": notice.get("show_on", "all"),
        }
        nav.append({"title": "Random article", "href": f"{root}random/"})
        return {"root": root, "site_name": self.config["site_name"], "nav": nav,
                "categories": cats, "footer": self.config.get("footer", ""),
                "disclaimer": disclaimer, "credits_href": f"{root}wiki/art-credits/",
                "has_icon": bool(self.config.get("icon"))}

    def render_article(self, art: Article) -> str:
        env = {"root": art.root, "where": art.title, "links": [], "article": art}
        infobox = self.render_infobox(art, env)
        body = self.render_body(art, env)
        if art.title == self.history_page:  # a small code marker ("X.4") on each section heading
            for code, sec in self.sections.items():
                if "." in code:
                    body = body.replace(f'<h3 id="{sec["anchor"]}">',
                                        f'<h3 id="{sec["anchor"]}"><span class="section-code">{code}</span> ', 1)
        cut = body.find("<h2")
        lead, rest = (body, "") if cut < 0 else (body[:cut], body[cut:])
        art.excerpt = first_sentence(plain_text(lead))
        art.text = search_text(body) + " " + search_text(infobox)  # prose first, for snippets
        after = self.chain_nav(art, env) + self.history_box(art, env)
        art.meta["_links"] = env["links"]
        cat = (self.config.get("categories") or {}).get(art.category)
        notice = (self.config.get("notices") or {}).get(art.title)
        if notice:  # a box above the lead, from config `notices`
            notice = {"label": notice.get("label", ""), "text": self.md.render(str(notice.get("text", "")), env)}
        sections, media = [], {}
        if art.title == MAIN_PAGE:  # the Main Page lays its sections out as cards
            sections = [s for s in re.split(r"(?=<h2)", rest) if s.strip()]
            rest = ""
            media = self.main_media()
        return self.jinja.get_template("article.html").render(
            **self.chrome(art.root), **self.meta(art.url, art),
            title=art.title,
            is_main=art.title == MAIN_PAGE,
            description=first_sentences(plain_text(lead)),
            category=cat and {"label": cat["singular"],
                              "href": f"{art.root}category/{FOLDERS[art.category]}/"},
            infobox=infobox, lead=lead, rest=rest, toc=self.toc(art),
            sections=sections, after=after, notice=notice, media=media,
        )

    def listed(self) -> list[Article]:
        """Articles that generated lists may show: everything but the hidden ones."""
        return [a for a in self.articles.values() if a.title not in self.hidden]

    def render_category(self, key: str) -> str:
        """An alphabetical index of one category, grouped by letter (a leading "The" is
        ignored for sorting), with period and region filters. Hidden articles are left out,
        unless config `hidden_on_category_pages` lists them on their own category page."""
        root = "../../"
        label = self.config["categories"][key]
        pool = self.articles.values() if self.hidden_on_category_pages else self.listed()
        arts = sorted((a for a in pool if a.category == key), key=sort_key)
        groups: dict[str, list] = {}
        periods, regions = set(), set()
        for art in arts:
            tags = art.meta.get("tags") or {}
            p, r = list(tags.get("period") or []), list(tags.get("region") or [])
            periods.update(p)
            regions.update(r)
            letter = sort_key(art)[:1].upper()
            groups.setdefault(letter if letter.isalpha() else "#", []).append({
                "title": art.title, "href": root + art.url, "excerpt": art.excerpt,
                "periods": "|".join(p), "regions": "|".join(r),
            })
        return self.jinja.get_template("category.html").render(
            **self.chrome(root), **self.meta(f"category/{FOLDERS[key]}/"), title=label["label"],
            description=f"Every {label['singular'].lower()} article in The Low Republic wiki.",
            count=len(arts), singular=label["singular"].lower(), groups=groups,
            periods=[p for p in PERIODS if p in periods] + sorted(periods - set(PERIODS)),
            regions=[r for r in REGIONS if r in regions] + sorted(regions - set(REGIONS)),
        )

    def render_page(self, title: str, root: str, body: str, description: str = "", path: str | None = None) -> str:
        """A generated page (art credits, not found) in the article layout."""
        return self.jinja.get_template("article.html").render(
            **self.chrome(root), **self.meta(path), title=title, is_main=False, description=description,
            category=None, infobox="", lead=body, rest="", toc=[], sections=[], after="", notice=None, media={})

    def render_credits(self) -> str:
        """Each artist, their link, and the articles their work appears in. The authors accepted
        that this lists some quarantined articles side by side (1 November 2026); hidden
        articles are never listed."""
        root = "../../"
        env = {"root": root, "where": "art credits", "links": []}
        artists = []
        for name, credit in sorted(self.credits.items(), key=lambda kv: kv[0].casefold()):
            works = sorted((self.articles[t] for t in credit["articles"]), key=sort_key)
            artists.append((name, {"link": credit["link"], "count": sum(credit["articles"].values()),
                                   "articles": [{"title": a.title, "href": root + a.url,
                                                 "count": credit["articles"][a.title]} for a in works]}))
        contact = self.config.get("art_credits") or {}
        return self.render_page("Art credits", root, self.jinja.get_template("_credits.html").render(
            artists=artists, contact_url=contact.get("contact_url", ""), contact_via=contact.get("contact_via", "")),
            "The artists whose work appears on The Low Republic wiki.", "wiki/art-credits/")

    def fresh(self, src: Path, dest: Path) -> bool:
        """True if dest exists and is newer than src (so it need not be made again)."""
        return dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime

    def main_media(self) -> dict:
        """The Main Page's video and map (config `main_page`), copied into media/.
        With ffmpeg, the video is rearranged so playback starts before the whole file
        has downloaded (no re-encoding) and a still frame is made to show before play."""
        cfg = self.config.get("main_page") or {}
        media = self.out / "media"
        media.mkdir(parents=True, exist_ok=True)
        found: dict = {}

        video = cfg.get("video") or {}
        src = ROOT / str(video.get("file") or "")
        if video.get("file") and not src.is_file():
            self.warn("config.yml", f"main_page video `{video['file']}` is not in the repository")
        elif video.get("file"):
            dest = media / src.name
            if not self.fresh(src, dest):
                done = FFMPEG and subprocess.run(
                    [FFMPEG, "-v", "error", "-y", "-i", str(src), "-c", "copy", "-movflags", "+faststart", str(dest)],
                    check=False).returncode == 0
                if not done:
                    shutil.copy2(src, dest)
            self.media_written.add(dest)
            when = float(video.get("poster_time", 0) or 0)
            poster = media / f"{src.stem}-poster-{when:g}s.jpg"
            if FFMPEG and not self.fresh(src, poster):
                subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", f"{when:g}", "-i", str(src), "-frames:v", "1",
                                "-vf", "scale=1280:-2", "-q:v", "3", str(poster)], check=False)
            size = (1920, 1080)
            if poster.exists():
                self.media_written.add(poster)
                with Image.open(poster) as im:
                    size = im.size
            else:
                print(f"note: no still image for {src.name} (ffmpeg not found); the video still works")
            found["video"] = {"src": f"media/{dest.name}", "title": video.get("title", ""),
                              "placement": str(video.get("placement") or "before_history"),
                              "poster": f"media/{poster.name}" if poster.exists() else "",
                              "width": size[0], "height": size[1]}

        mapcfg = cfg.get("map") or {}
        src = ROOT / str(mapcfg.get("file") or "")
        if mapcfg.get("file") and not src.is_file():
            self.warn("config.yml", f"main_page map `{mapcfg['file']}` is not in the repository")
        elif mapcfg.get("file"):
            original = media / "original" / src.name
            self._copy(src, original)
            with Image.open(src) as im:
                im = ImageOps.exif_transpose(im)
                width, height = im.size
                copies = []
                for target in MAP_WIDTHS:
                    w = min(target, width)
                    h = round(height * w / width)
                    dest = media / f"{src.stem}-{target}.webp"
                    if not self.fresh(src, dest):
                        im.convert("RGB").resize((w, h), Image.LANCZOS).save(dest, "WEBP", quality=86, method=4)
                    self.media_written.add(dest)
                    copies.append((f"media/{dest.name}", w, h))
            found["map"] = {"title": mapcfg.get("title", ""), "original": f"media/original/{src.name}",
                            "src": copies[0][0], "srcset": [c[0] for c in copies],
                            "width": copies[0][1], "height": copies[0][2],
                            "large": copies[-1][0], "large_w": copies[-1][1], "large_h": copies[-1][2]}
        return found

    def write_icons(self) -> None:
        """Every icon size from the one square PNG in config `icon`."""
        name = self.config.get("icon")
        if not name:
            return
        src = ROOT / str(name)
        if not src.is_file():
            self.warn("config.yml", f"icon `{name}` is not in the repository")
            return
        icons = self.out / "static" / "icons"
        icons.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as im:
            im = im.convert("RGBA")
            im.save(self.out / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
            for size in (16, 32, 192, 512):
                im.resize((size, size), Image.LANCZOS).save(icons / f"icon-{size}.png")
            # iPhones show transparency as black and round the corners themselves
            flat = Image.new("RGBA", im.size, PAGE_BACKGROUND)
            flat.alpha_composite(im)
            flat.convert("RGB").resize((180, 180), Image.LANCZOS).save(icons / "apple-touch-icon.png")
        manifest = {"name": self.config["site_name"], "short_name": self.config["site_name"],
                    "icons": [{"src": f"static/icons/icon-{s}.png", "sizes": f"{s}x{s}", "type": "image/png"}
                              for s in (192, 512)],
                    "theme_color": PAGE_BACKGROUND, "background_color": PAGE_BACKGROUND, "display": "browser"}
        (self.out / "site.webmanifest").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def write_search(self) -> None:
        """search/titles.json (titles and redirect names, for suggestions as you type),
        search/text.json (every article's plain text, for the results page), the results
        page itself, and random/, which opens a random article. The authors want every
        article findable by search, the hidden one included (it stays out of random/), and
        The Entire History left out of search altogether."""
        cats = self.config.get("categories") or {}
        titles, texts = [], []
        excluded = set(self.config.get("search_exclude") or [])
        for art in sorted(self.articles.values(), key=sort_key):
            if art.title in excluded:
                continue  # left out of search entirely (config `search_exclude`)
            redirects = []
            for entry in art.meta.get("redirects") or []:
                name, _, heading = str(entry).partition("#")
                anc = art.anchors.get(heading.strip(), "") if heading.strip() else ""
                redirects.append([name.strip(), anc])
            label = cats.get(art.category, {}).get("singular", "Page")
            titles.append({"t": art.title, "u": art.url, "c": label, "x": art.excerpt, "r": redirects})
            texts.append({"u": art.url, "h": [h for _, h, _ in art.headings], "b": art.text})
        dump = lambda data: json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        self.write("search/titles.json", dump(titles))
        self.write("search/text.json", dump(texts))
        self.write("search/index.html", self.jinja.get_template("search.html").render(
            **self.chrome("../"), **self.meta("search/"), title="Search", description="Search The Low Republic wiki."))
        pool = [a.url for a in self.listed() if a.category != "page"]
        self.write("random/index.html", self.jinja.get_template("random.html").render(urls=pool))

    def write_sitemap(self) -> None:
        """sitemap.xml for search engines: every listed article and page, the category pages
        and the credits page. Hidden articles and redirect stubs are left out."""
        base = self.site_url()
        if not base:
            return
        paths = [a.url for a in sorted(self.listed(), key=lambda a: (a.url != "", a.url))]
        paths += [f"category/{FOLDERS[k]}/" for k in self.config.get("categories") or {}] + ["wiki/art-credits/"]
        rows = "".join(f"  <url><loc>{html.escape(base + p)}</loc></url>\n" for p in paths)
        self.write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "</urlset>\n")
        self.write("robots.txt", f"User-agent: *\nDisallow: /random/\nDisallow: /search/\nSitemap: {base}sitemap.xml\n")

    def render_not_found(self) -> str:
        """404.html is served at whatever address was missing, so its links start from the
        site's own path (config `site_path`) instead of being relative."""
        root = str(self.config.get("site_path") or "/")
        env = {"root": root, "where": "404 page", "links": []}
        body = self.md.render(
            "There is no page at this address. It may have been renamed, or the link may be mistyped.\n\n"
            f"Try the search box at the top of the page, or start again from the [[{MAIN_PAGE}]].", env)
        return self.render_page("Page not found", root, body)

    # ---- writing ----------------------------------------------------------------

    def write(self, rel: str, text: str) -> None:
        dest = self.out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")

    def build(self) -> None:
        self.load()
        if self.out.exists():  # keep media/ so unchanged images are not resized again
            for child in self.out.iterdir():
                if child.name != "media":
                    shutil.rmtree(child) if child.is_dir() else child.unlink()
        self.out.mkdir(parents=True, exist_ok=True)

        for art in self.articles.values():
            self.write(art.url + "index.html", self.render_article(art))
        for key in self.config.get("categories") or {}:  # after the articles: needs their excerpts
            self.write(f"category/{FOLDERS[key]}/index.html", self.render_category(key))
        self.write("wiki/art-credits/index.html", self.render_credits())
        self.write_search()
        self.write_sitemap()
        self.write("404.html", self.render_not_found())

        redirect = self.jinja.get_template("redirect.html")
        for slug, (art, heading, name) in self.redirects.items():
            target = "../../" + art.url + "?from=" + urllib.parse.quote(name)
            if heading:
                target += "#" + art.anchors[heading]
            self.write(f"wiki/{slug}/index.html",
                       redirect.render(name=name, title=art.title, target=target))

        static = self.out / "static"
        shutil.copytree(HERE / "static", static, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("_*"))  # _fontface.css is merged into style.css
        for name, src in LOGOS.items():
            shutil.copy2(src, static / name)
        self.write_icons()
        (self.out / ".nojekyll").write_text("", encoding="utf-8")

        for path in (self.out / "media").rglob("*"):  # drop copies of images no longer used
            if path.is_file() and path not in self.media_written:
                path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Low Republic wiki.")
    parser.add_argument("--out", type=Path, default=HERE / "_site", help="output folder")
    parser.add_argument("--strict", action="store_true", help="exit with an error if anything is unresolved")
    args = parser.parse_args()

    config = yaml.safe_load((HERE / "config.yml").read_text(encoding="utf-8"))
    site = Site(config, args.out.resolve())
    try:
        site.build()
    except BuildError as exc:
        print(f"BUILD FAILED\n{exc}", file=sys.stderr)
        return 2

    print(f"Built {len(site.articles)} articles and pages and {len(site.redirects)} redirects "
          f"into {site.out}")
    in_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:  # a short report on the workflow run's page
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"### Wiki build\n\n{len(site.articles)} articles and pages, {len(site.redirects)} redirects, "
                     f"{len(site.warnings)} warning(s).\n\n")
            fh.writelines(f"- {w}\n" for w in site.warnings)
            fh.write("\n")
    if site.warnings:
        print(f"\n{len(site.warnings)} warning(s):")
        for w in site.warnings:
            print("  -", w)
            if in_actions:  # shown as a warning on the workflow run's page; it does not stop publishing
                print(f"::warning title=Wiki build::{w.replace('%', '%25')}")
        return 1 if args.strict else 0
    print("No warnings: every link, heading, redirect and image resolved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
