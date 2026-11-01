"""Rule checks on the built site in WIKI-SITE/_site/. Run after build.py:

    python WIKI-SITE/tests/check_site.py

Each check below is one rule from GAMEPLAN.md section 6. Any failure makes the
script exit with an error, which stops the GitHub workflow before it publishes,
so the live site stays on its last good version.

  links         every internal link, image, stylesheet and font points at a file
                that exists, and every #anchor exists on the page it points to
  completeness  every article, redirect, category and utility page was built, and
                each category page lists exactly its category's listed articles
  hidden        no page names or links to a hidden article, except its own page,
                its redirect stubs and (with `hidden_on_category_pages`) its own
                category page; it is out of random/, but in search
  quarantine    no generated box on a quarantined article links to another one
  search        search covers every article except those in `search_exclude`
  self-hosted   no page loads anything from another site (fonts included)
  previews      every article has link-preview tags with a picture on this site,
                and the sitemap lists every listed page (never a hidden one)
  disclaimer    every article carries the entry disclaimer, and configured
                notices appear on their articles
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent.parent
SITE = HERE / "_site"
sys.path.insert(0, str(HERE))
import build  # noqa: E402  (the generator: reused to know what should have been built)

ATTR_RE = re.compile(r'\b(?:href|src|poster)="([^"]+)"')
SRCSET_RE = re.compile(r'\bsrcset="([^"]+)"')
ID_RE = re.compile(r'\bid="([^"]+)"')
CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)")
IN_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"


class Checks:
    def __init__(self, out: Path = SITE, quiet: bool = False):
        self.out = Path(out)
        self.quiet = quiet
        self.config = yaml.safe_load((HERE / "config.yml").read_text(encoding="utf-8"))
        self.site = build.Site(self.config, self.out)
        self.site.load()  # the articles and redirects the site was built from
        self.pages = sorted(self.out.rglob("*.html"))
        self.text = {p: p.read_text(encoding="utf-8") for p in self.pages}
        self.ids = {p: set(ID_RE.findall(t)) for p, t in self.text.items()}
        self.results: list[tuple[str, list[str], str]] = []
        sitemap = self.out / "sitemap.xml"
        self.sitemap = sitemap.read_text(encoding="utf-8") if sitemap.exists() else ""

    def rel(self, path: Path) -> str:
        return path.relative_to(self.out).as_posix()

    def resolve(self, page: Path, ref: str) -> tuple[Path, str]:
        path, _, frag = ref.partition("#")
        path = urllib.parse.unquote(path.split("?")[0])
        if path.startswith("/"):  # root-relative: only the 404 page uses these
            site_path = str(self.config.get("site_path") or "/")
            path = path[len(site_path):] if path.startswith(site_path) else path.lstrip("/")
            target = (self.out / path).resolve()
        else:
            target = (page.parent / path).resolve() if path else page
        if target.is_dir():
            target = target / "index.html"
        return target, urllib.parse.unquote(frag)

    # ---- the rules -----------------------------------------------------------------

    def check_links(self):
        failures, count = [], 0
        for page, text in self.text.items():
            refs = ATTR_RE.findall(text)
            for srcset in SRCSET_RE.findall(text):
                refs += [part.split()[0] for part in srcset.split(",")]
            for ref in refs:
                if re.match(r"^[a-z]+:", ref) or ref.startswith("//"):
                    continue  # external
                count += 1
                target, frag = self.resolve(page, ref)
                if not target.exists():
                    failures.append(f"{self.rel(page)}: {ref} -> nothing at that address")
                elif frag and target.suffix == ".html" and frag not in self.ids.get(target, set()):
                    failures.append(f"{self.rel(page)}: {ref} -> no #{frag} on that page")
        css_files = list((self.out / "static").glob("*.css"))
        for css in css_files:
            for ref in CSS_URL_RE.findall(css.read_text(encoding="utf-8")):
                if not ref.startswith("data:") and not (css.parent / ref).exists():
                    failures.append(f"{self.rel(css)}: url({ref}) -> missing")
        return failures, f"{count} references on {len(self.pages)} pages, {len(css_files)} stylesheet(s)"

    def check_completeness(self):
        failures = []
        site = self.site
        for art in site.articles.values():
            if not (self.out / art.url / "index.html").exists():
                failures.append(f"{art.title}: no page at /{art.url}")
        for slug, (art, _, name) in site.redirects.items():
            page = self.out / "wiki" / slug / "index.html"
            if not page.exists():
                failures.append(f"redirect {name}: no stub at /wiki/{slug}/")
            elif f"../../{art.url}" not in self.text.get(page, ""):
                failures.append(f"redirect {name}: /wiki/{slug}/ does not lead to {art.title}")
        for extra in ("index.html", "404.html", "search/index.html", "random/index.html",
                      "wiki/art-credits/index.html"):
            if not (self.out / extra).exists():
                failures.append(f"/{extra} was not built")
        main = self.text.get(self.out / "index.html", "")
        media = self.config.get("main_page") or {}
        if (media.get("map") or {}).get("file") and 'class="article-body main-card main-card-wide main-map"' not in main:
            failures.append("the Main Page has no map (config main_page.map)")
        if self.config.get("icon") and not (self.out / "favicon.ico").exists():
            failures.append("no favicon.ico (config icon)")
        for key in self.config.get("categories") or {}:
            page = self.out / "category" / build.FOLDERS[key] / "index.html"
            if not page.exists():
                failures.append(f"category page for {key} was not built")
                continue
            listed = re.findall(r'class="category-title" href="\.\./\.\./([^"]+)"', self.text[page])
            expected = sorted(a.url for a in site.articles.values() if a.category == key
                              and (site.hidden_on_category_pages or a.title not in site.hidden))
            if sorted(listed) != expected:
                missing = set(expected) - set(listed)
                extra = set(listed) - set(expected)
                failures.append(f"category {key}: missing {sorted(missing)}, unexpected {sorted(extra)}")
        return failures, (f"{len(site.articles)} articles, {len(site.redirects)} redirects, "
                          f"{len(self.config.get('categories') or {})} category pages")

    def check_hidden(self):
        failures = []
        site = self.site
        titles = json.loads((self.out / "search" / "titles.json").read_text(encoding="utf-8"))
        random_page = self.text.get(self.out / "random" / "index.html", "")
        for title in sorted(site.hidden):
            art = site.articles.get(title)
            if art is None:
                failures.append(f"hidden article {title} does not exist")
                continue
            own = {self.out / art.url / "index.html"} | {
                self.out / "wiki" / slug / "index.html" for slug, (a, _, _) in site.redirects.items() if a is art}
            targets = {p.resolve() for p in own}
            allowed = set(own)
            if site.hidden_on_category_pages and art.category in build.FOLDERS:
                allowed.add(self.out / "category" / build.FOLDERS[art.category] / "index.html")
            names = [title] + [str(r).partition("#")[0].strip() for r in art.meta.get("redirects") or []]
            for page, text in self.text.items():
                if page in allowed:
                    continue
                # every link, however it is written, is resolved to the page it opens
                linked = any(self.resolve(page, ref)[0] in targets for ref in ATTR_RE.findall(text)
                             if not re.match(r"^[a-z]+:", ref) and not ref.startswith("//"))
                if linked or f"wiki/{art.slug}/" in text:  # the second test covers addresses in scripts
                    failures.append(f"{self.rel(page)} links to the hidden article {title}")
                lowered = text.lower()
                for name in names:
                    if name.lower() in lowered:
                        failures.append(f"{self.rel(page)} names the hidden article as \"{name}\"")
            if f"wiki/{art.slug}/" in random_page:
                failures.append(f"random/ can pick the hidden article {title}")
            if f"wiki/{art.slug}/" in self.sitemap:
                failures.append(f"sitemap.xml lists the hidden article {title}")
            if not any(e["u"] == art.url for e in titles):
                failures.append(f"{title} is missing from search (the authors want it findable)")
        return failures, f"{len(site.hidden)} hidden article(s) checked against {len(self.pages)} pages"

    def check_quarantine(self):
        failures = []
        site = self.site
        group = [site.articles[t] for t in sorted(site.quarantine) if t in site.articles]
        for art in group:
            text = self.text.get(self.out / art.url / "index.html", "")
            generated = text.split('<div class="article-after">', 1)[1] if '<div class="article-after">' in text else ""
            for other in group:
                if other is not art and f"wiki/{other.slug}/" in generated:
                    failures.append(f"{art.title}: a generated box links to {other.title}")
        return failures, f"{len(group)} quarantined articles"

    def check_search(self):
        failures = []
        site = self.site
        titles = json.loads((self.out / "search" / "titles.json").read_text(encoding="utf-8"))
        texts = json.loads((self.out / "search" / "text.json").read_text(encoding="utf-8"))
        excluded = set(self.config.get("search_exclude") or [])
        expected = sorted(a.url for a in site.articles.values() if a.title not in excluded)
        for name, data in (("titles.json", titles), ("text.json", texts)):
            urls = [e["u"] for e in data]
            if sorted(urls) != expected:
                failures.append(f"search/{name}: missing {sorted(set(expected) - set(urls))}, "
                                f"unexpected {sorted(set(urls) - set(expected))}")
            for url in urls:
                if not (self.out / url / "index.html").exists():
                    failures.append(f"search/{name}: /{url} has no page")
        return failures, f"{len(titles)} articles searchable, {len(excluded)} excluded"

    def check_self_hosted(self):
        failures = []
        for page, text in self.text.items():
            for tag in re.findall(r"<(?:link|script|img|iframe|video|source)\b[^>]*>", text):
                m = re.search(r'\b(?:href|src|poster)="((?:https?:)?//[^"]+)"', tag)
                if m and 'rel="canonical"' not in tag:  # the canonical link names the page itself
                    failures.append(f"{self.rel(page)} loads {m.group(1)}")
        for css in (self.out / "static").glob("*.css"):
            for ref in CSS_URL_RE.findall(css.read_text(encoding="utf-8")):
                if re.match(r"^(?:https?:)?//", ref):
                    failures.append(f"{self.rel(css)} loads {ref}")
        return failures, "pages and stylesheets load only the site's own files"

    def check_previews(self):
        """Every article has its link-preview tags; each preview picture and the sitemap's
        addresses point at real files on this site."""
        failures = []
        base = str(self.config.get("site_url") or "")
        if base and not base.endswith("/"):
            base += "/"
        if not base:
            return failures, "no site_url: previews skipped"

        def local(url):
            return self.out / url[len(base):] if url.startswith(base) else None

        for art in self.site.articles.values():
            text = self.text.get(self.out / art.url / "index.html", "")
            tags = dict(re.findall(r'<meta property="(og:[a-z:]+)" content="([^"]*)"', text))
            for key in ("og:title", "og:image", "og:url", "og:description"):
                if not tags.get(key):
                    failures.append(f"{art.title}: no {key}")
            if tags.get("og:url") and tags["og:url"] != base + art.url:
                failures.append(f"{art.title}: og:url is {tags['og:url']}")
            image = local(tags.get("og:image", ""))
            if tags.get("og:image") and (image is None or not image.exists()):
                failures.append(f"{art.title}: preview picture {tags['og:image']} is not on the site")
        listed = re.findall(r"<loc>([^<]+)</loc>", self.sitemap)
        if not listed:
            failures.append("sitemap.xml is missing or empty")
        for url in listed:
            path = local(url)
            if path is None or not (path / "index.html").exists():
                failures.append(f"sitemap.xml: {url} has no page")
        expected = {base + a.url for a in self.site.listed()}
        missing = expected - set(listed)
        if missing:
            failures.append(f"sitemap.xml is missing {sorted(missing)[:5]}")
        return failures, f"{len(self.site.articles)} pages with previews, {len(listed)} addresses in the sitemap"

    def check_disclaimer(self):
        failures = []
        site = self.site
        for art in site.articles.values():
            text = self.text.get(self.out / art.url / "index.html", "")
            if self.config.get("disclaimer") and 'id="disclaimer"' not in text:
                failures.append(f"{art.title}: no entry disclaimer")
        for title in (self.config.get("notices") or {}):
            art = site.articles.get(title)
            if art is None:
                failures.append(f"notices: no article titled {title}")
            elif 'class="notice"' not in self.text.get(self.out / art.url / "index.html", ""):
                failures.append(f"{title}: its notice box is missing")
        return failures, f"{len(site.articles)} pages, {len(self.config.get('notices') or {})} notice(s)"

    # ---- running ---------------------------------------------------------------------

    def say(self, line: str) -> None:
        if not self.quiet:
            print(line)

    def failed(self) -> set[str]:
        """The names of the checks that failed (run() first)."""
        return {name for name, failures, _ in self.results if failures}

    def run(self) -> int:
        checks = [("links", self.check_links), ("completeness", self.check_completeness),
                  ("hidden", self.check_hidden), ("quarantine", self.check_quarantine),
                  ("search", self.check_search), ("self-hosted", self.check_self_hosted),
                  ("previews", self.check_previews), ("disclaimer", self.check_disclaimer)]
        total = 0
        for name, check in checks:
            failures, detail = check()
            total += len(failures)
            self.say(f"{'PASS' if not failures else 'FAIL'}  {name:<13} {detail}")
            for f in failures[:50]:
                self.say(f"      - {f}")
                if IN_ACTIONS:  # shown as an error on the workflow run's page
                    print(f"::error title=Wiki check: {name}::{f.replace('%', '%25')}")
            if len(failures) > 50:
                self.say(f"      … and {len(failures) - 50} more")
            self.results.append((name, failures, detail))
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("### Wiki checks\n\n| Check | Result | Detail |\n|---|---|---|\n")
                for name, failures, detail in self.results:
                    fh.write(f"| {name} | {'✅ pass' if not failures else f'❌ {len(failures)} problem(s)'} | {detail} |\n")
        self.say("\nAll checks passed." if not total else f"\n{total} problem(s): the site will not be published.")
        return 1 if total else 0


if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else SITE
    sys.exit(Checks(folder).run())
