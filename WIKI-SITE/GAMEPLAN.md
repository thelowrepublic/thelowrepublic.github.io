# The Low Republic wiki: analysis and game plan

Status: **plan agreed 31 October 2026.** The decisions are recorded in section 8. Phase 1 (look and feel) is built and awaiting approval.

Everything for the website lives in this `WIKI-SITE/` folder. The one exception is the GitHub Actions workflow file, which GitHub requires to be in `.github/workflows/`. `ARTICLES/`, `ARTWORKS/` and the two logos are read-only input. The build never writes to them.

(The folder is not called `WORKFILES/` because `_FORMAT.md` already uses that name for the writing project's folder.)

---

## 1. What is in the repo

| Item | Finding |
|---|---|
| Articles | 120 files: 65 characters, 19 factions, 10 history, 21 places, 5 pages. About 94,000 words. The History alone is 21,700. |
| Status | 119 `approved`. Only Vesk Tolloran is `reviewed`. |
| Front matter | All 120 parse cleanly as YAML. Every value comes through as text, with no accidental numbers, dates or booleans. |
| Wiki-links | 2,643 links and 67 distinct section links. **Every title and every heading resolves.** |
| Redirects | 233 names on 66 articles. No clashes with titles, and every `Name#Heading` target exists. |
| Sources | 710 codes. Every chapter/section code maps to a heading on The History, and every `R:` code maps to an article. |
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
| `sources` | The **"In the history"** box at the foot of the article. Each code links to its section of The History, for example "X.4 · The Jedi who went". `R:` codes appear as "Register entry: Qi'ra" and link to that article, except where the quarantine forbids it (section 6). Pages do not get the box, because Timeline alone cites 84 codes. |
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

The site lives at `https://jakubpawelec.github.io/the-low-republic-wiki/`. All links are generated relative to that base, so a custom domain later is a one-line change.

| Page | URL |
|---|---|
| Main Page | `/` (the site root) |
| Any article or page | `/wiki/<file-slug>/`, for example `/wiki/padme-amidala/` or `/wiki/the-history/` |
| Redirect name | `/wiki/<redirect-slug>/`, a stub that forwards, for example `/wiki/darth-sidious/` |
| Category index | `/category/characters/`, `/category/factions/`, `/category/history/`, `/category/places/` |
| Search results | `/search/?q=...` |
| Art credits | `/wiki/art-credits/` (generated) |
| Not found | `404.html` |

The URLs are flat and use the slugs the authors already defined, so moving an article between folders (as with the Ossus split) never breaks a link.

### Page layout (desktop)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [THE LOW REPUBLIC  (wide logo)]                    [ Search the wiki…  ] │
├──────────────┬───────────────────────────────────────────────────────────┤
│ Main Page    │  Maul                                                     │
│ The History  │  Character                                                │
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
│ Hyerodrimm. Star Wars is © Lucasfilm and Disney. · Art credits           │
└──────────────────────────────────────────────────────────────────────────┘
```

- **Sidebar:** fixed links, the four categories, and the article's table of contents, which stays on screen as the reader scrolls (like Wikipedia's 2022 layout). Long pages such as The History and Timeline need it most.
- **Main Page:** keeps the authors' text untouched. The template adds the tall logo on top and lays the `##` sections ("The history", "The powers of the galaxy", "People", "Places", "Reference") out as cards in a two-column grid.
- **History articles:** the infobox shows "Preceded by" and "Followed by". A navigation bar at the foot repeats them as ← previous / next →. Where the chain branches, all branches are listed, as in The Death of Palpatine → The Long War · The Kamino Findings · The Reckoning of the Jedi.
- **The History:** chapter and section headings each carry a small grey code marker ("X.4"). Readers arriving from an "In the history" box can then see exactly where they landed.
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
| Accent (light grey) | `#c8c8cc` | heading rules, infobox title band, active contents entry, focus rings |
| Text | `#f4f4f4` | body text (white, a hair softened so it is easy on the eyes) |
| Muted | `#a6a6ad` | captions, infobox labels, hatnotes, credits |
| Link | `#8fb4ff` (pale blue) | links (D5) |
| Red link | `#ff8a80` | a link the build could not resolve |

- **Type:** a serif for the title and section headings, as Wikipedia does, and a clean sans-serif for body text. The logo stays the only Star Wars-style lettering.
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
4. **Index:** titles, slugs, the heading anchors of every article, redirects, and the chapter/section map of The History for source codes.
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

- **left out of:** every category page and filter, random article, sitemap, art credits page, backlinks ("What links here", if built), and every generated box or list. No page links to him on its own.
- **reachable by:** a direct URL (`/wiki/vesk-tolloran/`), the redirect stubs (`/wiki/agent-0006/`, `/wiki/moonraider/`), and search, **exactly like any other article**, suggestions and full text included (D7). The authors' aim is only that no article links to him directly, not that he is hard to find.

One caveat outside the website's reach: the repository itself is public. Anyone browsing it on GitHub can see `characters/vesk-tolloran.md`, and `ARTICLES/handoff-wiki-website.md` names both secrets outright. If that matters, the options are to make the repository private (Pages on a private repository needs a paid GitHub plan), or to move the brief out of the repository. Your call; it does not change the build.

### The Union quarantine

The eight articles are listed in `config.yml`. No generated feature may place two of them side by side or link one to another. Hand-written text, See also lists and infobox values written by the authors are left exactly as written. What the survey found:

- **Tags:** "Greater Seswenna Union" is the affiliation tag of six of the eight, plus Vesk Tolloran. An affiliation tag page would break both rules at once. This is decision D6.
- **"In the history" box:** The Greater Seswenna Union cites `R:Deran Kolt` and `R:Thrawn`, Thrawn cites `R:Deran Kolt`, and Deran Kolt cites `R:Thrawn`. Generated links there would join them, so on the quarantined articles those register entries are shown as plain text with no link.
- **Art credits:** one artist drew Dedra Meero, Orson Krennic and Thrawn. A credits page that listed each artist's articles would group three of them, so it lists artists and their portfolio links only. Each image is already credited in its own infobox.
- **Backlinks:** if a "What links here" feature is built, it drops any entry where both pages are in the quarantine.
- **Search results** answer the reader's own query and are not suggestions, so they are left alone. The History page is exempt, as the brief says.

### Automated checks after every build

- Vesk Tolloran's title, slug and URL appear in no generated page except his own page and his redirect stubs.
- No generated box, list or index on any quarantined article links to another quarantined article.
- Every link, section link, redirect, image and source code resolves.
- Every infobox image exists and has a web copy.

---

## 7. Phases

| # | Phase | What you get | Checkpoint |
|---|---|---|---|
| 0 | **Decisions** | Your answers to section 8. You confirm Settings → Pages → Source is **GitHub Actions**. | You reply |
| 1 | **Look and feel prototype** | The real templates and CSS, rendering four sample articles: Maul (portrait infobox), The Republic Corps (two image blocks), The Battle of Yavin (history infobox and chain) and Mandalore (emblem and place-style infobox). Desktop and phone screenshots sent here. | You approve the look |
| 2 | **The generator** | All 120 articles and pages built: infoboxes, figures, hatnotes, links, anchors, a canon tag, redirects. Clean link report. | Screenshots, spot checks |
| 3 | **Navigation and reference pages** | Sidebar and table of contents, Main Page layout, category pages, The History with code markers, Timeline, Glossary, history chain bar, "In the history" boxes, art credits, 404. | Screenshots |
| 4 | **Search** | Search box with suggestions (titles and redirects), a full results page, random article. | You try it |
| 5 | **Rules and tests** | Every check in section 6 automated, failing loudly if a rule is broken. | Test output |
| 6 | **Go live** | The Actions workflow. A pull request to `main` for you to merge, after which the site is live. A check on desktop and phone. | You merge |
| 7 | **Handover** | `WIKI-SITE/README.md`: how edits go live, how to preview locally, how to read the build report, how to change labels or the sidebar. | Done |

Work happens on the `claude/gifted-brown-x20p6v` branch. The site only goes live when you merge into `main`. Until then I'll show progress with screenshots taken in a headless browser.

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
| D11 | Image credits (authors' instruction) | Every infobox and figure ends with "Artwork by *author*", the name linked to `artwork_author_link`. The optional `image_caption` sits above that line. |

---

## 9. Small notes for the authors (no action needed by the build)

- **Boba Fett** and **Saw Gerrera** are linked from no other article and not from the Main Page. They will be reachable through the Characters category and search. Fine if intended.
- `ARTWORKS/art_credits_links.txt` spells two names differently from the files (`oleth_kar` for `oleth-kar.jpg`, `barris-offee` for `barriss-offee.jpg`). The site reads credits from the infoboxes, which are correct, so this has no effect.
- The Judicial Forces and the Sector Rangers bolds two names in its lead (both subjects), which is fine and renders normally.
