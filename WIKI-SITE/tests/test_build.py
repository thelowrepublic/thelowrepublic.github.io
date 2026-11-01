"""Unit tests for the generator (WIKI-SITE/build.py). They read the real articles
but write nothing to the repository.

    python -m unittest discover -s WIKI-SITE/tests
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402

CONFIG = yaml.safe_load((HERE / "config.yml").read_text(encoding="utf-8"))
_TMP = tempfile.TemporaryDirectory()
SITE = build.Site(CONFIG, Path(_TMP.name))
SITE.load()


def env(where="test"):
    return {"root": "../../", "where": where, "links": []}


def article(body: str, **meta) -> build.Article:
    """An article read from a temporary file, as the build would read it."""
    front = {"title": "Test Article", "category": "faction", "tier": "short", "batch": 0,
             "status": "draft", "sources": [], "canon": False}
    front.update(meta)
    path = Path(_TMP.name) / "test-article.md"
    path.write_text("---\n" + yaml.safe_dump(front, sort_keys=False) + "---\n" + body, encoding="utf-8")
    return build.read_article(path)


class Names(unittest.TestCase):
    def test_slugs_follow_the_format(self):  # the examples in _FORMAT.md section 1
        for title, slug in [("The Death of Palpatine", "the-death-of-palpatine"),
                            ("Padmé Amidala", "padme-amidala"), ("Do'Kass", "dokass"),
                            ("Salacious B. Crumb", "salacious-b-crumb"), ("Yavin 4", "yavin-4")]:
            self.assertEqual(build.title_slug(title), slug)

    def test_every_file_is_named_after_its_title(self):
        for art in SITE.articles.values():
            self.assertEqual(build.title_slug(art.title), art.slug, art.path.name)

    def test_anchors(self):
        self.assertEqual(build.anchor("The schism, 14–8 BBY"), "the-schism-14-8-bby")
        self.assertEqual(build.anchor("Ko Sai's procedure"), "ko-sais-procedure")
        self.assertEqual(build.unique_anchors(["Aftermath", "Aftermath"]), ["aftermath", "aftermath-2"])

    def test_redirect_slugs_are_url_safe(self):
        self.assertEqual(build.url_slug("Yavin 4 dig"), "yavin-4-dig")
        self.assertEqual(build.url_slug("Agent 0006"), "agent-0006")


class Reading(unittest.TestCase):
    def test_windows_line_endings_and_trailing_spaces(self):
        art = article("Lead.  \r\n\r\n## Section \r\n\r\nText.\r\n")
        self.assertEqual(art.headings, [(2, "Section", "section")])
        self.assertNotIn("\r", art.body)

    def test_all_articles_parse(self):
        self.assertEqual(len(SITE.articles), 120)
        self.assertIn(CONFIG["history_page"], SITE.articles)


class WikiLinks(unittest.TestCase):
    def render(self, text):
        e = env()
        return SITE.inline(text, e), e

    def test_plain_and_piped(self):
        out, _ = self.render("[[Maul]] and [[Maul|the warlord]]")
        self.assertIn('<a href="../../wiki/maul/">Maul</a>', out)
        self.assertIn('<a href="../../wiki/maul/">the warlord</a>', out)

    def test_section_link_shows_the_section(self):
        out, _ = self.render("[[The Death of Palpatine#The escape of Maul]]")
        self.assertIn('href="../../wiki/the-death-of-palpatine/#the-escape-of-maul"', out)
        self.assertIn("The Death of Palpatine § The escape of Maul", out)

    def test_escaped_pipe_in_a_table_cell(self):
        out, _ = self.render(r"[[Maul\|the warlord]]")
        self.assertIn(">the warlord</a>", out)

    def test_unknown_title_is_a_red_link_and_a_warning(self):
        before = len(SITE.warnings)
        out, _ = self.render("[[Nobody At All]]")
        self.assertIn('class="redlink"', out)
        self.assertEqual(len(SITE.warnings), before + 1)
        del SITE.warnings[before:]


class Body(unittest.TestCase):
    def test_hatnote(self):
        art = article("Lead.\n\n## History\n\n*Main article: [[Maul]]*\n\nText.\n")
        html = SITE.render_body(art, env(art.title))
        self.assertIn('<div class="hatnote" role="note">Main article: <a href="../../wiki/maul/">Maul</a></div>', html)

    def test_image_block_moves_to_the_top_of_the_section_it_closes(self):
        art = article("Lead.\n\n## First\n\n*Main article: [[Maul]]*\n\nOne.\n\nTwo.\n\n"
                      "```image\nimage: \"maul.jpg\"\nimage_caption: \"\"\nartwork_author: \"\"\n"
                      "artwork_author_link: \"\"\n```\n\n## Second\n\nThree.\n")
        html = SITE.render_body(art, env(art.title))
        figure, hatnote, second = html.index("<figure"), html.index('class="hatnote"'), html.index('id="second"')
        self.assertLess(hatnote, figure)  # after the heading and its hatnote...
        self.assertLess(figure, html.index("<p>One.</p>"))  # ...before the section's text
        self.assertLess(figure, second)  # and never beside the next section

    def test_default_and_unknown_credits(self):
        e = env()
        official = SITE.image_box({"image": "maul.jpg", "artwork_author": ""}, e, "alt", "figure")
        unknown = SITE.image_box({"image": "ilai-vess.jpg", "artwork_author": ""}, e, "alt", "figure")
        named = SITE.image_box({"image": "maul.jpg", "artwork_author": "A", "artwork_author_link": "https://a.example"}, e, "alt", "figure")
        self.assertIn("Artwork by " + CONFIG["default_artwork_author"], official)
        self.assertIn("Artwork by " + CONFIG["unknown_artist_label"], unknown)
        self.assertIn('Artwork by <a href="https://a.example"', named)

    def test_canon_tag_on_background(self):
        art = article("Lead.\n\n## Background\n\nCanon text.\n", canon=True)
        self.assertIn('class="tag"', SITE.render_body(art, env(art.title)))


class HistoryBox(unittest.TestCase):
    def box(self, title):
        art = SITE.articles[title]
        return SITE.history_box(art, {"root": "../../", "where": title, "links": []})

    def test_passages_link_into_the_history_page(self):
        html = self.box("Maul")
        self.assertIn('<span class="section-code">I.4</span> The escape of Maul', html)
        self.assertIn("wiki/the-entire-history/#the-escape-of-maul", html)

    def test_register_entries_respect_the_quarantine(self):
        html = self.box("The Greater Seswenna Union")  # cites R:Deran Kolt and R:Thrawn
        self.assertNotIn("wiki/deran-kolt/", html)
        self.assertNotIn("wiki/thrawn/", html)
        self.assertIn("Deran Kolt", html)

    def test_own_register_entry_is_bold_not_a_link(self):
        html = self.box("Oleth Kar")
        self.assertIn("<strong>Oleth Kar</strong>", html)
        self.assertNotIn("wiki/oleth-kar/", html)

    def test_pages_have_no_box(self):
        self.assertEqual(self.box("Timeline"), "")


class Text(unittest.TestCase):
    def test_first_sentence(self):
        self.assertEqual(build.first_sentence("Born c. 30 BBY in the Core, she rose. Then she fell."),
                         "Born c. 30 BBY in the Core, she rose.")

    def test_search_text_drops_images_and_headings(self):
        html = '<p><a href="x">Dathomir</a>.</p><h2 id="a">Heading</h2><figure><figcaption>Artwork by Y</figcaption></figure><p>End</p>'
        self.assertEqual(build.search_text(html), "Dathomir. End")

    def test_sort_ignores_a_leading_the(self):
        self.assertEqual(build.sort_key(SITE.articles["The Galactic Republic"]), "galactic republic")

    def test_svg_size(self):
        self.assertEqual(build.svg_size(build.ARTWORKS / "the-galactic-republic.svg"), (600, 600))


class Lists(unittest.TestCase):
    def test_hidden_articles_are_not_listed(self):
        listed = {a.title for a in SITE.listed()}
        self.assertTrue(SITE.hidden)
        self.assertFalse(SITE.hidden & listed)


if __name__ == "__main__":
    unittest.main()
