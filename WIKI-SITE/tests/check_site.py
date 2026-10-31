"""Checks on the built site in WIKI-SITE/_site/. Run after build.py:

    python WIKI-SITE/tests/check_site.py

- every internal link, image and stylesheet points at a file that exists,
  and every #anchor exists on the page it points to
- no page links to a hidden article except its own page and its redirect stubs
- no generated box on a quarantined article links to another quarantined article

Pages that later phases will add (category pages, search) are reported
separately as "not built yet" rather than as failures.
"""

from __future__ import annotations

import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent.parent
SITE = HERE / "_site"
NOT_YET = ("search/",)  # added in Phase 4

ATTR_RE = re.compile(r'\b(?:href|src)="([^"]+)"')
SRCSET_RE = re.compile(r'\bsrcset="([^"]+)"')
ID_RE = re.compile(r'\bid="([^"]+)"')


def main() -> int:
    config = yaml.safe_load((HERE / "config.yml").read_text(encoding="utf-8"))
    pages = sorted(SITE.rglob("*.html"))
    ids = {p: set(ID_RE.findall(p.read_text(encoding="utf-8"))) for p in pages}
    failures: list[str] = []
    not_yet: dict[str, int] = defaultdict(int)
    checked = 0

    for page in pages:
        text = page.read_text(encoding="utf-8")
        refs = ATTR_RE.findall(text)
        for srcset in SRCSET_RE.findall(text):
            refs += [part.split()[0] for part in srcset.split(",")]
        for ref in refs:
            if re.match(r"^[a-z]+:", ref) or ref.startswith("//"):
                continue  # external
            checked += 1
            path, _, frag = ref.partition("#")
            path = urllib.parse.unquote(path.split("?")[0])
            if path.startswith("/"):  # root-relative (only the 404 page uses these)
                site_path = str(config.get("site_path") or "/")
                path = path[len(site_path):] if path.startswith(site_path) else path.lstrip("/")
                target = (SITE / path).resolve()
            else:
                target = (page.parent / path).resolve() if path else page
            if target.is_dir():
                target = target / "index.html"
            rel = target.relative_to(SITE.resolve()).as_posix() if target.is_relative_to(SITE.resolve()) else str(target)
            if not target.exists():
                if rel.startswith(NOT_YET):
                    not_yet[rel.split("/")[0] + "/" + rel.split("/")[1] + "/"] += 1
                else:
                    failures.append(f"{page.relative_to(SITE)}: {ref} -> missing {rel}")
                continue
            if frag and target.suffix == ".html" and urllib.parse.unquote(frag) not in ids.get(target, set()):
                failures.append(f"{page.relative_to(SITE)}: {ref} -> no #{frag} on {rel}")

    # hidden articles: nothing links to them but their own page and redirect stubs
    for title in config.get("hidden") or []:
        slug = re.sub(r"[^a-z0-9-]", "", title.lower().replace(" ", "-"))
        needle = f"wiki/{slug}/"
        for page in pages:
            rel = page.relative_to(SITE).as_posix()
            if rel == f"wiki/{slug}/index.html":
                continue
            text = page.read_text(encoding="utf-8")
            if needle in text and 'http-equiv="refresh"' not in text:
                failures.append(f"{rel}: links to the hidden article {title}")

    # Union quarantine: generated parts (the boxes after the article text) never join two of them
    quarantine = config.get("quarantine") or []
    slugs = {t: re.sub(r"[^a-z0-9-]", "", t.lower().replace(" ", "-")) for t in quarantine}
    for title, slug in slugs.items():
        page = SITE / "wiki" / slug / "index.html"
        if not page.exists():
            failures.append(f"quarantined article {title} was not built")
            continue
        text = page.read_text(encoding="utf-8")
        generated = text.split('<div class="article-after">', 1)[1] if '<div class="article-after">' in text else ""
        for other, other_slug in slugs.items():
            if other != title and f"wiki/{other_slug}/" in generated:
                failures.append(f"wiki/{slug}/: a generated box links to {other} (Union quarantine)")

    print(f"Checked {checked} internal references on {len(pages)} pages.")
    for where, n in sorted(not_yet.items()):
        print(f"  not built yet (later phase): {where} ({n} links)")
    if failures:
        print(f"\n{len(failures)} problem(s):")
        for f in failures:
            print("  -", f)
        return 1
    print("All internal links, anchors and images resolve; no page links to a hidden article;"
          " no generated box joins two quarantined articles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
