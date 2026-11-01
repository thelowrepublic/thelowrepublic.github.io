# The Low Republic wiki: analysis and game plan

Status: **plan agreed 31 October 2026.** The decisions are recorded in section 8. All seven phases are done: look and feel, the generator, navigation and reference pages, search, the automated rule checks, going live, and the handover guide (`WIKI-SITE/README.md`). The site is live at https://thelowrepublic.github.io/ and republishes on every push to `main`.

The repository moved on 31 October 2026 from `JakubPawelec/the-low-republic-wiki` to `thelowrepublic/thelowrepublic.github.io`, so that the address carries no personal account name. The old address no longer works.

Everything for the website lives in this `WIKI-SITE/` folder. The one exception is the GitHub Actions workflow file, which GitHub requires to be in `.github/workflows/`. `ARTICLES/`, `ARTWORKS/` and the two logos are read-only input. The build never writes to them.

(The folder is not called `WORKFILES/` because `_FORMAT.md` already uses that name for the writing project's folder.)

---

## 1. What is in the repo

| Item | Finding |
|---|---|
| Articles | 120 files: 65 characters, 19 factions, 10 history, 21 places, 5 pages. About 94,000 words. The Entire History alone is 21,700. |
| Status | 119 `approved`. Only Vesk Tolloran is `reviewed`. |
| Front matter | All 120 parse cleanly as YAML. Every value comes through as text, with no accidental numbers, dates or booleans. |
| Wiki-links | 2,643 links and 67 distinct section links. **Every title and every heading resolves.** |
| Redirects | 233 names on 66 articles. No clashes with titles, and every `Name#Heading` target exists. |
| Sources | 710 codes. Every chapter/section code maps to a heading on The Entire History, and every `R:` code maps to an article. |
| Images | 42 infobox images and 5 body image blocks. All 47 files exist and none are unused. 37 JPG, 7 SVG, 2 WebP, 1 PNG. **No captions are filled in yet.** |
| Markdown used | Paragraphs, `##`/`###`, bullet lists and hatnotes everywhere. Only Main Page has a block quote and a numbered list, and only Glossary has a table. No raw HTML, no em dashes, no stray italics. |
| Logos | `lowrepubliclogowide.png` (2100×213) and `lowrepubliclogotall.png` (1017×296). Both are light grey on transparent, which suits a dark theme. |
| GitHub Pages | The repo is public and Pages is **enabled** (`has_pages: true`). No deployment has run yet, and there are no workflows. That fits Pages being set to build from **GitHub Actions**, which is what this plan needs (see 8, D1). |

The full numbers are in `analysis/survey-report.md`, produced by `analysis/survey.py`.

### Things the build has to handle

1. **Mixed line endings.** 36 files have Windows (CRLF) line endings, and 11 have lines ending in spaces. The build normalises both before reading, so a hatnote with a trailing space is still a hatnote.
2. **Dark emblems on a dark page.** The Mandalore, Nightsisters and Shadow Collective SVGs are black on transparent and almost vanish on a dark background. The Jedi Templars emblem is dark brown. See `analysis/emblems-on-dark.png`. They are shown as they are; the authors will replace the files with versions on a white background (D4).
3. **Image weight.** The artwork totals about 13 MB, and `dedra-meero.png` alone is 2.4 MB. The build makes resized web copies for the page and links each one to the full-size original. The originals are not touched.
4. **Empty captions.** Nothing is captioned yet, so the boxes must look finished without one. A caption appears automatically once the authors fill it in.
5. **Files that are not articles.** `_FORMAT.md` and `handoff-wiki-website.md` sit at the root of `ARTICLES/`. The build reads only the five category folders, so neither is ever published.

---

## 2. How each part of an article becomes a wiki page

| In the `.md` file | On the page |
|---|---|
| `title` | The page heading (H1) and the browser tab title. |
| `category` | A small label under the title ("Character", "Faction" and so on), linking to that category's index. It also picks the infobox labels. |
| `tier` | Not shown. Used to sort lists (hubs and majors first where that helps). |
| `batch`, `status` | Not shown. Every article is published; Vesk Tolloran's `reviewed` status makes no difference (D8). |
| `canon: true` | A small grey **Canon** tag beside the `## Background` heading, linking to Canon and sources § How the articles use canon. |
| `tags` | Feeds the period and region filters on the category pages (D6). Never used to suggest articles. |
| `redirects` | A search name, plus a tiny forwarding page at `/wiki/<redirect-slug>/` that sends the reader to the article (and to the section, for `Name#Heading`). The article then shows "(Redirected from *Name*)", as Wikipedia does. |
| `infobox` | The box floated to the top right, described in section 4. |
| `sources` | The **"In the history"** box at the foot of the article. Each code links to its section of The Entire History, for example "X.4 · The Jedi who went". `R:` codes appear as "Register entry: Qi'ra" and link to that article, except where the quarantine forbids it (section 6). Pages do not get the box, because Timeline alone cites 84 codes. |
| Lead (text before the first heading) | Rendered as is. The bold subject name stays bold. |
| `## Section` / `### Subsection` | H2 / H3, each with a stable anchor made from its text: `The schism, 14–8 BBY` becomes `#the-schism-14-8-bby`. These anchors drive the table of contents and every `[[Title#Heading]]` link. |
| `*Main article: [[X]]*` directly under a heading | A hatnote: indented, smaller and grey, like Wikipedia's. A section link displays as "The Death of Palpatine § The escape of Maul". |
| `[[Title]]`, `[[Title\|text]]`, `[[Title#Heading]]`, `[[Title#Heading\|text]]` | Ordinary links to `/wiki/<slug>/` or `/wiki/<slug>/#<anchor>`. A link with no display text and a heading shows "Title § Heading". A link that does not resolve is shown in red and reported in the build log. Today there are none. |
| ` ```image ` block | A figure floated right, the same width family as the infobox, with the optional caption and the "Artwork by *author*" credit. It moves to the top of the section it closes (D3). |
| `## See also` | A plain bulleted list, as written. |
| Tables (Glossary), block quote and numbered list (Main Page) | Styled to match: a bordered wiki-table, and an indented quote with a grey bar. |

---

## 3. Site structure

### URLs

The site lives at `https://thelowrepublic.github.io/`. All links are relative, so a custom domain later needs no code change. Only the not-found page uses the site's own path (`site_path` in `config.yml`).

| Page | URL |
|---|---|
| Main Page | `/` (the site root) |
| Any article or page | `/wiki/<file-slug>/`, for example `/wiki/padme-amidala/` or `/wiki/the-history/` |
| Redirect name | `/wiki/<redirect-slug>/`, a stub that forwards, for example `/wiki/darth-sidious/` |
| Category index | `/category/characters/`, `/category/factions/`, `/category/history/`, `/category/places/` |
| Search results | `/search/?q=...` |
| Art credits | `/wiki/art-credits/` (generated: each artist, their link and the articles their work appears in) |
| Not found | `404.html` |

The URLs are flat and use the slugs the authors already defined, so moving an article between folders (as with the Ossus split) never breaks a link.

### Page layout (desktop)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [THE LOW REPUBLIC  (wide logo)]                    [ Search the wiki…  ] │
├──────────────┬───────────────────────────────────────────────────────────┤
│ Main Page    │  Maul                                                     │
│ The Entire History  │  Character                                                │
│ Timeline     │  ═════════════════════════════════════════════════════    │
│ Glossary     │  Maul is the Zabrak warlord at the head    ┌────────────┐ │
│ Canon and    │  of the Shadow Collective, a galaxy-       │    Maul    │ │
│  sources     │  spanning criminal empire. A son of …      │ ┌────────┐ │ │
│ Random       │                                            │ │portrait│ │ │
│              │  Background  [Canon]                       │ └────────┘ │ │
│ BROWSE       │  ───────────────────────────────           │ Art: m.saad│ │
│ History      │  Maul was a Dathomirian Zabrak …           │ Species  … │ │
│ Factions     │                                            │ Homeworld …│ │
│ Characters   │  The escape, 19 BBY                        │ Born     … │ │
│ Places       │  ───────────────────────────────           └────────────┘ │
│              │    Main article: The Death of Palpatine § The escape …    │
│ CONTENTS     │  Four days before Palpatine's killing, …                  │
│ (follows the │  …                                                        │
│  reader as   │  See also                                                 │
│  they scroll)│  ┌ In the history ─────────────────────────────────────┐  │
│              │  │ I.4 The escape of Maul · IV.2 The bargain · …       │  │
│              │  │ Register entries: Qi'ra · Nadi Orl · Sarn Vekh · …   │  │
│              │  └─────────────────────────────────────────────────────┘  │
├──────────────┴───────────────────────────────────────────────────────────┤
│ The Low Republic is a fan-made alternate universe by Pablito and         │
│ HyeroDrimm. Star Wars is © Lucasfilm and Disney. · Art credits           │
└──────────────────────────────────────────────────────────────────────────┘
```

- **Sidebar:** fixed links, the four categories, and the article's table of contents, which stays on screen as the reader scrolls (like Wikipedia's 2022 layout). Long pages such as The Entire History and Timeline need it most.
- **Main Page:** keeps the authors' text untouched. The template adds the tall logo on top and lays the `##` sections ("The history", "The powers of the galaxy", "People", "Places", "Reference") out as cards in a two-column grid.
- **History articles:** the infobox shows "Preceded by" and "Followed by". A navigation bar at the foot repeats them as ← previous / next →. Where the chain branches, all branches are listed, as in The Death of Palpatine → The Long War · The Kamino Findings · The Reckoning of the Jedi.
- **The Entire History:** chapter and section headings each carry a small grey code marker ("X.4"). Readers arriving from an "In the history" box can then see exactly where they landed.
- **Category pages:** an alphabetical list with each article's first sentence. Filters by period and region (D6).
- **Mobile (under about 750 px):** the sidebar becomes a menu button, the table of contents becomes a collapsible "Contents" block under the lead, and the infobox and figures stop floating and sit full width in the text flow. The lead comes first, then the infobox, as on Wikipedia's mobile site, so a reader is not met by a full-screen portrait before the first sentence.

---

## 4. Look and feel

Minimal and Wikipedia-shaped, in dark mode. These are starting values, to be tuned on the prototype (Phase 1):

| Token | Value | Used for |
|---|---|---|
| Background | `#0f0f10` | the page |
| Surface | `#18181a` | infobox, figures, "In the history" box, tables |
| Border | `#3a3a3e` | box outlines, table rules |
| Accent (light grey) | `#c8c8cc` | sidebar links and small labels (text) |
| Detail (Tatooine sand) | `#c8b992` | every light element that is not text: infobox title bands, the line under page titles (full) and section headings (55%), the active contents entry, quote and notice bars, the Acknowledge button, the menu icon, focus rings (D27) |
| Text | `#f4f4f4` | body text (white, a hair softened so it is easy on the eyes) |
| Muted | `#a6a6ad` | captions, infobox labels, hatnotes, credits |
| Link | `#8fb4ff` (pale blue) | links (D5) |
| Red link | `#ff8a80` | a link the build could not resolve |

- **Type:** Orbitron for the title, section headings and infobox titles, and Barlow for body text (D21). The logo stays the only Star Wars-style lettering.
- **Infobox:** about 300 px wide, floated right with a 1.5 em gap on the left so text wraps cleanly. From top to bottom: a light grey title band (the `name`, or the title), the image (natural shape), the optional `image_caption`, then the credit line "Artwork by *author*" with the author's name linked to `artwork_author_link`, then label/value rows. With no link the name is plain text; with no author there is no credit line. List values sit one per line. Fields that are not present are simply not drawn.
- **Image figures:** the same frame as the infobox, about 260 px wide. They use `clear: right`, so they stack below the infobox instead of squeezing beside it.
- **Section rules:** the thin line under each `##` heading stops at the edge of a floated box instead of running under it.
- **Labels:** each infobox key gets a fixed display label, for example `also_known_as` "Also known as", `senate_stance` "Senate stance", `schism_camp` "Schism camp", `key_figures` "Key figures", `held_by` "Held by", `affiliated_with` "Affiliated with" and `preceded_by` "Preceded by". The label list lives in one config file, so it is easy to adjust.
- **Contrast:** every text colour meets WCAG AA against its background.

---

## 5. Technical approach

### Stack: a small Python generator, deployed by GitHub Actions

| Option | Verdict |
|---|---|
| Jekyll (GitHub Pages' built-in builder) | No. Wiki-links, image blocks, infobox rendering and the two hidden-content rules would all need custom plugins, which Pages' built-in builder does not run. It would also mean reshaping the articles into Jekyll's folder rules. |
| JavaScript app that fetches the `.md` files in the browser | No. The raw files, including Vesk Tolloran's, would have to be published as-is, backlinks and quarantine checks would run in every visitor's browser, and pages would be slow to appear and invisible to search engines. |
| **Custom Python static generator + Actions (recommended)** | Full control over every rule in the format. It produces plain HTML pages that load instantly, and it reports broken links on every build. Python matches the authors' existing tools (`lint.py`, `build_history.py`). It needs only PyYAML, markdown-it-py, Jinja2 and Pillow. |

### Files

```
WIKI-SITE/
  GAMEPLAN.md            this document
  README.md              for the authors: how edits go live, how to preview locally
  build.py               the generator
  config.yml             labels, sidebar links, hidden article, quarantine list
  requirements.txt       pinned Python packages
  templates/             Jinja2 page templates (base, article, main page, category, redirect, search, 404)
  static/                style.css, search.js, small UI scripts, favicon
  tests/                 checks run after every build (section 6)
  analysis/              this survey
.github/workflows/pages.yml   build and deploy on every push to main
.gitignore                    ignores _site/ (build output, never committed)
```

### What `build.py` does, in order

1. **Find** every `.md` in `ARTICLES/{history,factions,characters,places,pages}/`, skipping any name that starts with `_`.
2. **Normalise:** UTF-8 with any BOM stripped, CRLF changed to LF, and trailing spaces removed.
3. **Parse** the front matter. A file that does not parse stops the build, so the live site stays on the last good version and no article silently disappears.
4. **Index:** titles, slugs, the heading anchors of every article, redirects, and the chapter/section map of The Entire History for source codes.
5. **Render each body:** lift out image blocks, mark hatnotes, resolve wiki-links, convert the Markdown, give headings their anchors, and tag the canon Background.
6. **Render the boxes:** the infobox, the "In the history" box, and the history chain.
7. **Generate site-wide pages:** Main Page, category pages, redirect stubs, the search index, the random-article list, art credits, 404 and sitemap.
8. **Images:** resize the artwork into web copies with Pillow (about 320 and 640 px wide), copy the SVGs and the logos, and link each image to its original.
9. **Check:** run the rule checks in section 6 and print a link report. Problems show as warnings in the Actions log and as red links on the page.
10. **Write** everything to `_site/`.

### Deploying

- `.github/workflows/pages.yml` runs on every push to `main` and can also be started by hand. It installs Python, runs `build.py`, runs the tests, and publishes `_site/` to Pages. It takes about a minute.
- **For the authors:** edit a `.md` file on GitHub (or push it), and the site updates itself about a minute later. Nothing else to do.
- **Local preview:** `python WIKI-SITE/build.py`, then `python -m http.server -d _site`. This works on Windows too. The README will spell it out.

---

## 6. The two special rules

### The hidden article (Vesk Tolloran)

The hidden article and its redirect names are listed in `config.yml`. It will be:

- **left out of:** random article, sitemap, art credits page, backlinks ("What links here", if built), and every generated box or list. No other article links to him on its own.
- **listed on:** the Characters category page, like any other character (D35; config `hidden_on_category_pages`).
- **reachable by:** a direct URL (`/wiki/vesk-tolloran/`), the redirect stubs (`/wiki/agent-0006/`, `/wiki/moonraider/`), and search, **exactly like any other article**, suggestions and full text included (D7). The authors' aim is only that no article links to him directly, not that he is hard to find.

One caveat outside the website's reach: the repository itself is public. Anyone browsing it on GitHub can see `characters/vesk-tolloran.md`, and `ARTICLES/handoff-wiki-website.md` names both secrets outright. If that matters, the options are to make the repository private (Pages on a private repository needs a paid GitHub plan), or to move the brief out of the repository. Your call; it does not change the build.

### The Union quarantine

The eight articles are listed in `config.yml`. No generated feature may place two of them side by side or link one to another. Hand-written text, See also lists and infobox values written by the authors are left exactly as written. What the survey found:

- **Tags:** "Greater Seswenna Union" is the affiliation tag of six of the eight, plus Vesk Tolloran. An affiliation tag page would break both rules at once. This is decision D6.
- **"In the history" box:** The Greater Seswenna Union cites `R:Deran Kolt` and `R:Thrawn`, Thrawn cites `R:Deran Kolt`, and Deran Kolt cites `R:Thrawn`. Generated links there would join them, so on the quarantined articles those register entries are shown as plain text with no link.
- **Art credits:** one artist drew Dedra Meero, Orson Krennic and Thrawn, so the credits page lists three of them together. The authors accepted this on 1 November 2026. Hidden articles are left off the page.
- **Backlinks:** if a "What links here" feature is built, it drops any entry where both pages are in the quarantine.
- **Search results** answer the reader's own query and are not suggestions, so they are left alone. The Entire History page is exempt, as the brief says.

### Automated checks after every build

Every push to `main` runs, in order: the build, the rule checks (`tests/check_site.py`), and the tests (`python -m unittest discover -s WIKI-SITE/tests -t WIKI-SITE/tests`). A failed rule check or test stops the workflow before it publishes, so the live site stays on its last good version, and the failures appear as errors on the workflow run's page.

| Check | Rule |
|---|---|
| links | Every internal link, image, stylesheet and font points at a file that exists, and every `#anchor` exists on its page. |
| completeness | Every article, redirect, category page and utility page was built; each category page lists exactly its category's listed articles. |
| hidden | No page links to a hidden article (every link is resolved, however it is written) or names it by its title or redirect names, except its own page, its redirect stubs and its own category page (D35). It is never in `random/`, and it is in search (D7). |
| quarantine | No generated box on a quarantined article links to another quarantined article. |
| search | Search covers every article except those in `search_exclude` (D24). |
| self-hosted | No page loads anything from another site, fonts included. |
| previews | Every article has its link-preview tags with a picture that exists on the site; the sitemap lists every listed page and never a hidden one (D30). |
| disclaimer | Every article carries the entry disclaimer, and every configured notice appears on its article. |

`tests/test_build.py` checks the generator's rules directly (slugs, anchors, links, hatnotes, image placement, credits, the "In the history" box, search text). `tests/test_checks.py` breaks each rule in a copy of the built site and expects the matching check to fail, so a check that silently stopped working would be caught. That test found and fixed one gap on 1 November 2026: a link written as `../vesk-tolloran/` slipped past the first version of the hidden check.

Problems that are the authors' to fix, such as a wiki-link to a title that does not exist, are **warnings**: the page shows a red link, the workflow run's page lists the warning, and the site still publishes.

---

## 7. Phases

| # | Phase | What you get | Checkpoint |
|---|---|---|---|
| 0 | **Decisions** | Your answers to section 8. You confirm Settings → Pages → Source is **GitHub Actions**. | You reply |
| 1 | **Look and feel prototype** | The real templates and CSS, rendering four sample articles: Maul (portrait infobox), The Republic Corps (two image blocks), The Battle of Yavin (history infobox and chain) and Mandalore (emblem and place-style infobox). Desktop and phone screenshots sent here. | You approve the look |
| 2 | **The generator** | All 120 articles and pages built: infoboxes, figures, hatnotes, links, anchors, a canon tag, redirects. Clean link report. | Screenshots, spot checks |
| 3 | **Navigation and reference pages** | Sidebar and table of contents, Main Page layout, category pages, The Entire History with code markers, Timeline, Glossary, history chain bar, "In the history" boxes, art credits, 404. | Screenshots |
| 4 | **Search** | Search box with suggestions (titles and redirects), a full results page, random article. | You try it |
| 5 | **Rules and tests** | Every check in section 6 automated, failing loudly if a rule is broken. | Test output |
| 6 | **Go live** | The Actions workflow. A pull request to `main` for you to merge, after which the site is live. A check on desktop and phone. | You merge |
| 7 | **Handover** | `WIKI-SITE/README.md`: how edits go live, how to preview locally, how to read the build report, how to change labels or the sidebar. | Done |

Work happens on the `claude/gifted-brown-x20p6v` branch and is merged into `main` when each step is ready (authors' permission, 31 October 2026). The publishing workflow from Phase 6 was brought forward so the site can be browsed while it is built; the rest of Phase 6 (final checks on desktop and phone) still comes at the end.

---

## 8. Decisions (settled 31 October 2026)

| # | Question | Decision |
|---|---|---|
| D1 | How the site is built | Python generator, deployed by GitHub Actions. Pages' source is set to "GitHub Actions". |
| D2 | URL shape | `/wiki/padme-amidala/`, flat, using the authors' slugs. |
| D3 | Where image blocks appear | Each figure moves to the top of the section it closes (after the heading and any hatnote), so it sits beside the text about it. |
| D4 | Dark emblems | Shown as they are, with no plate. The authors will replace the files that disappear with versions on a white background. |
| D5 | Link colour | Pale blue `#8fb4ff`. |
| D6 | Tag-based pages | No affiliation pages. Category pages get period and region filters only. |
| D7 | Finding the hidden article | Ordinary search, like any other article. He is kept out of generated lists and links only. |
| D8 | Hidden article extras | No `noindex`. He is published despite his `reviewed` status. |
| D9 | "In the history" box | At the foot of each article, after See also. Not on the five pages. |
| D10 | "What links here" pages | Left out for now. They can be added later with both rules applied. |
| D11 | Image credits (authors' instruction) | Every infobox and figure ends with "Artwork by *author*", the name linked to `artwork_author_link`. The optional `image_caption` sits above that line. An image with no `artwork_author` is credited to "Lucasfilm and Disney" (`default_artwork_author` in `config.yml`), except images listed in `unknown_artist_images` (Ilai Vess's), which get no credit line. |
| D12 | Clicking an image (authors' instruction) | Opens a lightbox: the page darkens, the image is scaled to the window's height (a 1600 px web copy), "Open full image" at the image's top right opens the original in a new tab, and the credit sits underneath. A click on the dark background, or Esc, closes it. |
| D13 | Entry disclaimer (authors' instruction) | A full-screen notice with an Acknowledge button: non-commercial fan work, Star Wars owned by Lucasfilm and Disney, other material owned by its authors, artwork credited where possible, artists may ask the owner to alter or remove their work. It appears on the first page a new visitor opens and is remembered in that browser; the footer's "Disclaimer" link shows it again. Text, contact line and version live in `config.yml`. |
| D14 | Per-image placement | Where the authors want a figure beside a different section, the image block is moved in the article itself, as was done for the Death Watch image in The Shadow Collective (31 October 2026), now closing "How the Collective thrives". |
| D15 | Images by an unknown artist (authors' instruction) | Credited "Artwork by unknown artist" (`unknown_artist_label`), for the images listed in `unknown_artist_images`. The article keeps its empty artist keys, as the format requires. |
| D16 | Main Page | The authors' text, untouched: the tall logo, the lead and quote (as wide as the cards below, authors' instruction), the first section as a full-width card, the next section in the left column and the rest stacked on the right. Phones show one column. |
| D17 | "In the history" box | Passages are listed in the history's own order, each with its code ("X.4") and linking to that section of The Entire History. Register entries link to the figure's article, except an article's own entry (shown in bold), a hidden article, or another quarantined article on a quarantined page (plain text). |
| D18 | Category pages | Alphabetical, ignoring a leading "The", grouped by letter with a jump bar; each entry shows the lead's first sentence; period and region filters. Hidden articles are listed on their own category page (D35). |
| D19 | The history page (authors' instruction, 1 November 2026) | Renamed from "The History" to **The Entire History** (`pages/the-entire-history.md`), with "The History" kept as a redirect. A "Before you read" box above its first paragraph says it holds the entire lore and advises reading the individual articles instead (`notices` in `config.yml`). It sits in the sidebar between Glossary and Canon and sources. |
| D20 | Art credits page (authors' instruction, 1 November 2026) | Each artist with their link, image count and the articles their work appears in. Hidden articles are never listed. |
| D21 | Fonts (authors' choice, 1 November 2026) | **Orbitron** for headings, infobox titles and the disclaimer title; **Barlow** for all other text. Both are self-hosted from `WIKI-SITE/static/fonts/` (SIL Open Font License, licence files alongside), so visitors' browsers make no requests to Google. |
| D22 | Search (Phase 4) | Suggestions under the search box as you type, from titles and redirect names, ignoring capitals, accents and apostrophes. A redirect name is shown ("Darth Sidious → The Death of Palpatine") only when the title itself does not match. Enter opens an exact title or redirect match, otherwise the results page (`/search/?q=`), which ranks every article containing all the words, with highlighted snippets from the prose. Every article is searchable, Vesk Tolloran included (D7), except The Entire History (D24). Data: `search/titles.json` (26 KB) and `search/text.json` (about 550 KB, loaded only on the results page). |
| D23 | Random article | A sidebar link to `/random/`, which opens a random article: not the five pages, and never a hidden article. |
| D24 | The Entire History and search (authors' instruction, 1 November 2026) | Left out of search entirely: no suggestions, no results (`search_exclude` in `config.yml`). |
| D25 | Tab icon (authors' file, 1 November 2026) | `lowrepublicicon.png` (512 px, dark rounded square with "LR") in the main folder. The build makes `favicon.ico` (16, 32, 48 px), 16 and 32 px PNGs, the 180 px iPhone icon (on the page colour) and 192 and 512 px icons with a web manifest for Android (config `icon`). |
| D26 | Main Page video and map (authors' instruction, 1 November 2026; video removed by D36) | `lowrepubliccrawl.mp4` sits between the opening text and "The history", 720 px wide, with controls and sound; it never plays by itself and loads only its header until played. With ffmpeg the build rearranges the site's copy so it starts promptly (no re-encoding) and takes the still image from 2 seconds in. `lowrepublicmap.jpg` closes the page as a full-width box titled "Map of the galaxy", shown at the box's width (readers scroll down through it); clicking it opens the lightbox and the full-size original. Both are set in config `main_page`. |
| D27 | Detail colour (authors' choice, 1 November 2026) | **Tatooine sand `#C8B992`** for every light element that is not text, as in Mockup A; the logos keep their own light grey. Chosen over Star Wars yellow `#FFE81F`, which was too bright for the palette. Set once as `--detail` in `style.css`. |
| D28 | Author's name (authors' instruction, 1 November 2026) | Spelled **HyeroDrimm** everywhere: the site footer and the articles Canon and sources and The Entire History. |
| D29 | Contact (authors' instruction, 1 November 2026) | Not in the disclaimer. The Art credits page ends with "please contact the owner of this wiki on Discord", linked to the owner's Discord profile (config `art_credits`). |
| D30 | Link previews and sitemap (1 November 2026) | Every page carries Open Graph and Twitter tags with its full address (config `site_url`) and its first sentence. The preview picture is the article's own artwork when it is a JPG, PNG or WebP, otherwise the card `WIKI-SITE/assets/social-card.png` (wide logo, sand line, "WIKI"; config `social_image`). `sitemap.xml` lists every listed article and page, the category pages and the credits page; `robots.txt` points to it. Hidden articles are in neither. |
| D31 | Planet pictures (authors' files, 1 November 2026) | 18 WebP images in `ARTWORKS/`, named after their place articles, are each article's infobox image, credited explicitly to "Lucasfilm and Disney" as the format does for official art. Murkhana and Nal Kaddan have no picture yet; Galactic regions has no infobox. |
| D32 | Emblem outlines (authors' instruction, 1 November 2026) | `the-shadow-collective.svg` and `the-nightsisters.svg` carry the same thin white outline as `mandalore.svg` (`stroke="#fff" stroke-width="4"` on their shape, with the viewBox widened by 2 units on each side so the outline is never clipped). |
| D33 | Main Page video position (authors' instruction, 1 November 2026; superseded by D36) | Moved between the logo and the opening text. `placement` in config `main_page.video` switches it: `below_logo`, or `before_history` for its first position above "The history". |
| D34 | Final look-over (1 November 2026) | All 127 pages loaded at desktop and phone size: no script errors, failed requests, broken images or horizontal overflow. Every text style on 16 page states meets WCAG AA (lowest 6.72:1). Fixed: on phones the "Before you read" notice now stays above the opening text, and search snippets no longer include "Main article:" lines. |
| D35 | Vesk Tolloran on the Characters page (authors' instruction, 1 November 2026) | The hidden article is listed on its own category page like any other article (config `hidden_on_category_pages: true`). He stays out of random article, the sitemap, art credits and every generated box, and no other article links to him. The checks expect him on Characters and nowhere else. |
| D36 | Main Page video removed (authors' instruction, 1 November 2026) | The video is gone from the Main Page and `lowrepubliccrawl.mp4` is deleted from the repository, along with the code that showed it, its settings, its check and the workflow's ffmpeg step. The map stays. The last version with the video is commit 97774d5, if it is ever wanted back. |
| D37 | New emblems and a new article (authors' files, 1 November 2026) | Order of Voss and Republic Intelligence have emblems, credited explicitly to Lucasfilm and Disney. `republic-intelligence.svg` (drawn in black) gets the thin white outline of D32; its outer ring, a drawn line rather than a filled shape, gets a white ring beneath it instead, and its open inner shape is closed so the outline runs all round. The Corporate Security Alliance (Wolfdog's artwork, added to `ARTWORKS/art_credits_links.txt`) uses a new affiliation tag, added to the format's vocabulary. The publish had failed only because a test expected exactly 120 articles; it now counts the article files, and the tests' deliberately broken copies no longer post errors to the run page. |
| D38 | Jedi Templars emblem outline (authors' instruction, 1 November 2026) | `the-jedi-templars.svg` gets the thin white outline of D32. Its shape sits inside two scaling transforms (3.21 in all), so the outline is 1.2463 in the shape's own units, 4 in the image's, like the other emblems; a viewBox adds 2 units of room on every side at the same scale. |

---

## 9. Small notes for the authors (no action needed by the build)

- **Boba Fett** and **Saw Gerrera** are linked from no other article and not from the Main Page. They will be reachable through the Characters category and search. Fine if intended.
- `ARTWORKS/art_credits_links.txt` spells two names differently from the files (`oleth_kar` for `oleth-kar.jpg`, `barris-offee` for `barriss-offee.jpg`). The site reads credits from the infoboxes, which are correct, so this has no effect.
- The Judicial Forces and the Sector Rangers bolds two names in its lead (both subjects), which is fine and renders normally.
