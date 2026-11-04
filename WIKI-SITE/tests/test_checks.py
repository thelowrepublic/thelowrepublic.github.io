"""Tests for the rule checks themselves: each test breaks one rule in a copy of the
built site and expects exactly that check to fail. Run after build.py:

    python -m unittest discover -s WIKI-SITE/tests
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
BUILT = HERE / "_site"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_site  # noqa: E402


@unittest.skipUnless((BUILT / "index.html").exists(), "build the site first (python WIKI-SITE/build.py)")
class RuleChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.clean = Path(cls.tmp.name) / "clean"
        shutil.copytree(BUILT, cls.clean, ignore=shutil.ignore_patterns("media"))
        (cls.clean / "media").symlink_to(BUILT / "media", target_is_directory=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.site = Path(self.tmp.name) / self.id().rsplit(".", 1)[-1]
        shutil.copytree(self.clean, self.site, symlinks=True)

    def tearDown(self):
        shutil.rmtree(self.site)

    def edit(self, rel, old, new):
        path = self.site / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"{rel} has changed shape; update this test")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def failed(self):
        checks = check_site.Checks(self.site, quiet=True)
        checks.run()
        return checks.failed()

    def test_the_clean_build_passes(self):
        self.assertEqual(self.failed(), set())

    def test_links_catch_a_missing_page(self):
        shutil.rmtree(self.site / "wiki" / "dathomir")
        self.assertIn("links", self.failed())

    def test_links_catch_a_missing_anchor(self):
        self.edit("wiki/maul/index.html", 'id="background"', 'id="renamed"')
        self.assertIn("links", self.failed())

    def test_completeness_catches_a_missing_category_entry(self):
        self.edit("category/characters/index.html", 'class="category-title" href="../../wiki/maul/"',
                  'class="category-gone" href="../../wiki/maul/"')
        self.assertIn("completeness", self.failed())

    def test_hidden_catches_a_name_on_another_page(self):
        self.edit("category/places/index.html", "</ul>", "<li>Vesk Tolloran</li></ul>")
        self.assertIn("hidden", self.failed())

    def test_completeness_catches_the_hidden_article_missing_from_its_category(self):
        self.edit("category/characters/index.html", 'class="category-title" href="../../wiki/vesk-tolloran/"',
                  'class="category-gone" href="../../wiki/vesk-tolloran/"')
        self.assertIn("completeness", self.failed())

    def test_hidden_catches_a_link(self):
        self.edit("wiki/maul/index.html", "</article>", '<a href="../vesk-tolloran/">?</a></article>')
        self.assertIn("hidden", self.failed())

    def test_hidden_catches_the_random_page(self):
        self.edit("random/index.html", 'var pages = ["', 'var pages = ["wiki/vesk-tolloran/", "')
        self.assertIn("hidden", self.failed())

    def test_quarantine_catches_a_generated_link(self):
        self.edit("wiki/the-secessions/index.html", '<div class="article-after">',
                  '<div class="article-after"><a href="../../wiki/thrawn/">Thrawn</a>')
        self.assertIn("quarantine", self.failed())

    def test_search_catches_an_entry_with_no_page(self):
        path = self.site / "search" / "titles.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data.append({"t": "Nowhere", "u": "wiki/nowhere/", "c": "Page", "x": "", "r": []})
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("search", self.failed())

    def test_search_catches_a_missing_article(self):
        path = self.site / "search" / "text.json"
        data = [e for e in json.loads(path.read_text(encoding="utf-8")) if e["u"] != "wiki/maul/"]
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("search", self.failed())

    def test_self_hosted_catches_an_outside_font(self):
        self.edit("wiki/maul/index.html", "</head>",
                  '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron"></head>')
        self.assertIn("self-hosted", self.failed())

    def test_previews_catch_a_missing_picture(self):
        self.edit("wiki/maul/index.html", '<meta property="og:image" ', '<meta property="og:gone" ')
        self.assertIn("previews", self.failed())

    def test_hidden_catches_the_sitemap(self):
        self.edit("sitemap.xml", "</urlset>",
                  "  <url><loc>https://thelowrepublic.github.io/wiki/vesk-tolloran/</loc></url>\n</urlset>")
        self.assertIn("hidden", self.failed())

    def test_disclaimer_catches_a_page_without_it(self):
        self.edit("wiki/maul/index.html", 'id="disclaimer"', 'id="something-else"')
        self.assertIn("disclaimer", self.failed())


if __name__ == "__main__":
    unittest.main()
