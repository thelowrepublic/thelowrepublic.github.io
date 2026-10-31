# ARTICLE FORMAT

This file explains how every article in this folder is built. It is not an article. Any file whose name begins with `_` is documentation and should be skipped by the website.

The article list and what each article covers are in `WORKFILES/wiki-article-structure-v3.md`. This file covers only the form.

---

## 1. Folders and file names

```
ARTICLES/
  _FORMAT.md        this file
  history/          the 10 history articles
  factions/         the 19 faction and group articles
  characters/       the 65 character articles
  places/           the 21 place articles
  pages/            Main Page, Timeline, Glossary, Canon and sources, The History
```

- **Artwork** lives outside this folder, in `ARTWORKS/` at the project root.
  - It is one flat folder of JPG, PNG, WebP and SVG files.
  - An article's main image is named after the article's slug (`maul.jpg`). Extra images for the body add a word for their subject (`the-republic-corps-marshal.jpg`).
  - `ARTWORKS/art_credits_links.txt` lists the artists and their links.

- One article per file. Every file is Markdown (`.md`) in UTF-8.
- **The file name is the slug of the title.** Lowercase the title, strip accents, remove apostrophes and full stops, and turn every space into a hyphen.

  | Title | File |
  |---|---|
  | The Death of Palpatine | `the-death-of-palpatine.md` |
  | Padmé Amidala | `padme-amidala.md` |
  | Do'Kass | `dokass.md` |
  | Salacious B. Crumb | `salacious-b-crumb.md` |
  | Yavin 4 | `yavin-4.md` |

- The folder must match the article's `category`.

---

## 2. File layout

Every article has two parts, always in this order:

1. **Front matter**: a YAML block between two `---` lines at the very top. It holds the metadata and the infobox.
2. **Body**: the article text in Markdown.

This is the shape of a character article. Angle brackets mark placeholders.

```markdown
---
title: <Article title>
category: character
tier: standard
batch: <n>
status: draft
sources: [<II.3>, <XII.11>, "R:<Article title>", "R:<Other register entry>"]
canon: true
tags:
  affiliation: [<Affiliation>]
  period: [<Period>, <Period>]
  region: [<Region>]
redirects: [<Other name>, "<Topic>#<Heading in this article>"]
infobox:
  image: ""
  image_caption: ""
  artwork_author: ""
  artwork_author_link: ""
  name: <Full name>
  species: <Species>
  born: <NN BBY> (aged <NN>)
  affiliation: ["[[<Article title>]]"]
  position: <Role at the end of 2 ABY>
  formerly: ["[[<Article title>|<display text>]]"]
---

<Lead paragraph. The **subject's name** is in bold at its first appearance.>

## Background

<Canon background, short.>

## <Career section>

<Text.>

## In 2 ABY

<Present tense.>

## See also

- [[<Article title>]]
```

---

## 3. Front matter

### 3.1 YAML rules

The front matter uses a deliberately small part of YAML, so any parser can read it and it always looks the same.

- One `key: value` per line. No value runs over two lines.
- Lists are written inline: `[a, b, c]`.
- Only `tags` and `infobox` contain nested keys, indented by two spaces.
- **Quote any value** that contains `:`, `#`, `[`, `]`, `,`, `"` or `|`, or that starts with `*`, `&` or `!`. This includes every value that holds a wiki-link. Use double quotes.
- Leave out a key that has no value. The exceptions are `image`, `image_caption`, `artwork_author` and `artwork_author_link`, which are always present and stay `""` until filled.

### 3.2 Keys, in this order

| Key | Required | Value |
|---|---|---|
| `title` | yes | The article title exactly as listed in the structure doc. Links use this text. |
| `category` | yes | `history`, `faction`, `character`, `place` or `page` |
| `tier` | yes | `hub`, `major`, `standard`, `short` or `stub`. Pages use `none`. |
| `batch` | yes | The writing batch number (from `WORKFILES/writing-gameplan.md`) |
| `status` | yes | `draft` (written), `reviewed` (second reader done and fixes applied) or `approved` (signed off by the authors) |
| `sources` | yes | Every masterdoc passage used (3.3). |
| `canon` | yes | `true` if the article has a canon-based Background section, otherwise `false`. |
| `tags` | yes, except pages | `affiliation`, `period` and `region` lists (3.4). Pages leave it out. |
| `redirects` | no | Other names that should lead here (3.5). |
| `infobox` | for most | See Section 4. Composite overviews have no infobox. |

### 3.3 Source codes

- `II.3` is chapter II, section 3. The full key is in Section 8 of the structure doc.
- `R:Title` is a register entry. It is keyed by the article title of the person the entry is about, for example `"R:Oleth Kar"`, `"R:Rex"` or `"R:Thrawn"`. Ki-Adi-Mundi and Stass Allie share one entry, and either title points to it.
- `XV` is the closing chapter. It is cited only for the few details found nowhere else.

The website builds each article's "In the history" box from this list, so the body does not repeat it.

### 3.4 Tags

Use only these values.

- **affiliation:**
  - Galactic Republic
  - Republic Intelligence
  - Jedi Order (before 0 ABY)
  - Jedi Templars
  - Ossus Order
  - Order of Voss
  - Shadow Collective
  - Nightborn
  - Nightsisters
  - Greater Seswenna Union
  - Dathomir-Yavin Accord
  - Kashyyyk Region Coalition
  - Hutt Clans
  - Mandalore
  - Path of Light
  - Confederacy
  - Independent
- **period:** `Before 19 BBY`, `Long War` (19–15 BBY), `15 BBY–0 ABY`, `Shadow War` (0–2 ABY). Use every period the article covers.
- **region:** Core, Inner Rim, Mid Rim, Outer Rim, Hutt Space, Wild Space

### 3.5 Redirects

These are search names that lead to this article. A plain name leads to the top of the article. `Name#Heading` leads to a section of this article.

```yaml
redirects: [Palpatine, Darth Sidious, "The escape of Maul#The escape of Maul"]
```

---

## 4. Infoboxes

The infobox sits in the front matter under `infobox:`. The website draws it as the box at the top right of the page.

- **Every infobox starts with four image keys, in this order:**
  - `image`: the file name in `ARTWORKS/`, with no folder, such as `"maul.jpg"`.
  - `image_caption`: the caption shown under the image. The authors write the captions.
  - `artwork_author`: the name of the artist, so the website can credit them.
  - `artwork_author_link`: a link to the artist's page or to the artwork's source. A URL contains `:`, so it is always quoted.

  The keys are always present. A key with no value yet stays `""`.
- **Credits** come from `ARTWORKS/art_credits_links.txt`:
  - Where the artist is unknown, both artist keys stay `""` (Ilai Vess).
  - A Star Wars logo that has no artist in the file is credited to `Lucasfilm and Disney`, with no link.
- **The infobox image** is the file named exactly after the article. Any other images of the article go in the body (5.6).
- **Values come only from the article's sources or the canon notes.** Fields without a value are left out, never filled with "Unknown". The exception is where the masterdoc itself says so, as with Thrawn's age, "unrecorded".
- **Values are short.** Dates and ages may use figures (`46 BBY`, `48`). Prose uses words, as the masterdoc does.
- **Values may contain wiki-links.** These must be quoted (3.1).
- **List-type fields** take a list even when there is only one item.

### 4.1 Character

| Key | Type | Notes |
|---|---|---|
| `name` | text | Full name as the masterdoc gives it. |
| `also_known_as` | list | Other names and titles. |
| `designation` | text | Clones only. |
| `species` | text | Organic characters. |
| `model` | text | Droids and machines only (C-3PO, R2-D2, Kalani, Patient Yield). |
| `homeworld` | text | Only if the masterdoc or the canon notes state it. |
| `born` | text | Birth year and age at the end of 2 ABY, together: `46 BBY (aged 48)`, or `c. 30 BBY (aged about 32)` when approximate. Clones give their physical age: `32 BBY (physically 68)`. A character who has died gives the year only. See 4.1.1. |
| `died` | text | Date, and place if stated. |
| `affiliation` | list | At the end of 2 ABY. |
| `position` | text | Role at the end of 2 ABY. |
| `formerly` | list | Earlier affiliations and posts. |
| `senate_stance` | text | Politicians only. |
| `schism_camp` | text | Jedi only, where the masterdoc states it: `reformist`, `traditionalist` or `withdrawalist`. |

#### 4.1.1 Where `born` comes from

Every character infobox has a `born` field unless no source gives a birth year. Look in this order, and stop at the first that answers.

1. **The masterdoc.** Its birth year and age always win, for example a register entry's `(b. 46 BBY, aged 48)`. Where the masterdoc itself says the age is unknown (Thrawn's "age unrecorded", Ren-Vashal's "age not stated"), use its words: `born: Age unrecorded`.
2. **Wookieepedia's Canon page.** Use the birth year in its infobox. Record it in the batch's canon notes as a `- Born:` line. Work the age out to the end of 2 ABY: a birth year in BBY plus two. A clone's physical age is twice that. If the canon year clashes with an age or date in the masterdoc, ask the authors before using it.
3. **Neither.** Leave `born` out, and record `- Born: none` in the canon notes, so the gap is known to be checked.

A character who has died gives the birth year alone in `born`. The `died` field gives the year of death, and the place if a source states it.

### 4.2 Faction

| Key | Type | Notes |
|---|---|---|
| `type` | text | For example: State, Military, Law enforcement, Intelligence service, Jedi order, Force order, Criminal organisation, Sector alliance, Sect, Population group. |
| `also_known_as` | list | |
| `founded` | text | |
| `founder` | list | |
| `leader` | list | At the end of 2 ABY. |
| `seat` | text | Capital, base or headquarters. |
| `territory` | text | |
| `strength` | text | At the end of 2 ABY, in the masterdoc's figure, for example `about 600`. |
| `affiliated_with` | list | Only ties the masterdoc states. |
| `predecessor` | text | |
| `status` | text | At the end of 2 ABY, for example `Active` or `Disbanded 12 BBY`. |

**The combined article** Mandalore uses the place infobox and adds `leader`, `strength` and `founded` where relevant. Its `type` names both, as a place and as a faction. (Ossus and Voss were combined articles until the authors split them on 16 October 2026.)

### 4.3 History

| Key | Type | Notes |
|---|---|---|
| `type` | text | For example: Event, War, Battle, Law, Census, Political crisis. |
| `date` | text | |
| `place` | text | |
| `participants` | list | |
| `key_figures` | list | |
| `drafted_by` | list | Laws only. |
| `carried_by` | list | Laws only. |
| `result` | text | One line. |
| `losses` | text | Only figures the masterdoc gives. |
| `preceded_by` | list | The history article or articles this one follows on from, by date. |
| `followed_by` | list | The history article or articles that come next, by date. Where several threads branch off at once, list them all. An article at the end of a thread leaves the key out. |

#### 4.3.1 The history chain

Chronological order wins. The masterdoc is one continuous read, but the wiki can branch: one article can lead into several threads that run at the same time. (Authors' decision, 15 October 2026.) Every history article uses this chain:

| Article | `preceded_by` | `followed_by` |
|---|---|---|
| The Death of Palpatine | | The Long War, The Kamino Findings, The Reckoning of the Jedi |
| The Long War | The Death of Palpatine | The Republic Remade |
| The Kamino Findings | The Death of Palpatine | The Manumission Act |
| The Manumission Act | The Kamino Findings | The Republic Remade |
| The Republic Remade | The Long War, The Manumission Act | The Census of 4 BBY |
| The Census of 4 BBY | The Republic Remade | The Battle of Yavin |
| The Reckoning of the Jedi | The Death of Palpatine | The Battle of Yavin |
| The Battle of Yavin | The Reckoning of the Jedi, The Census of 4 BBY | The Shadow War, The Secessions |
| The Shadow War | The Battle of Yavin | |
| The Secessions | The Battle of Yavin | |

### 4.4 Place

| Key | Type | Notes |
|---|---|---|
| `type` | text | Planet, Moon, Region and so on. |
| `also_known_as` | list | |
| `region` | text | |
| `sector` | text | |
| `held_by` | list | At the end of 2 ABY. |
| `population` | text | Only if stated. |
| `locations` | list | Named sites on it, for example the Jedi Temple or the Massassi temples. |

### 4.5 No infobox

Three kinds of article have no `infobox` key at all:
- the composite overviews **Galactic regions** and **Three Stances of the Senate**
- all `pages/` files

---

## 5. Body

### 5.1 Headings

- **No `#` heading in the body.** The website shows the title from the front matter.
- `##` marks sections and `###` marks subsections. Nothing deeper is used.
- **Headings are link targets.** A heading named in Section 5 of the structure doc must keep that exact text.
- **History articles use the masterdoc's own section headings, in full** (for example `## The schism, 14–8 BBY`). They add only the extra subheadings listed in the structure doc.

### 5.2 Section order

| Category | Order |
|---|---|
| history | lead, `## Background` (if canon), the masterdoc's sections in order, `## See also` |
| faction | lead, `## Background` (if canon), history sections in date order, sections on structure or doctrine, `## In 2 ABY`, `## See also` |
| character | lead, `## Background` (if canon), career sections in date order, `## In 2 ABY`, `## See also` |
| place | lead, `## Background` (if canon), `## History`, `## In 2 ABY`, `## See also` |
| stub | lead, `## Background` (if canon, a few sentences from the canon notes), then `## See also` if useful |

- **The lead** is the text before the first heading: two to four sentences that make sense on their own. The subject's name is in **bold** at its first appearance.
- **Background** holds canon material only. It is short and comes from `WORKFILES/canon-notes.md`, never from memory.
- **In 2 ABY** is in the present tense. It describes the state of things at the end of 2 ABY.
- **No "Personality", "Motivations", "Powers and abilities", "Trivia", "Behind the scenes" or "Unanswered questions" sections.**

### 5.3 Links

| Form | Meaning |
|---|---|
| `[[Title]]` | Link to an article. `Title` is the exact `title` of the target. |
| `[[Title\|text]]` | The same link, showing different text. |
| `[[Title#Heading]]` | Link to a section. `Heading` is the exact heading text. |
| `[[Title#Heading\|text]]` | The same section link, showing different text. |

- Always link to the real title, never a redirect name. A character without an article is linked through the article that covers them: `[[The Death of Palpatine|Palpatine]]`.
- A topic that is folded into another article is linked to its section, as listed in Section 5 of the structure doc: `[[The Secessions#The Vess case|the Vess case]]`.
- Link a subject at its first mention in the lead, and again at its first mention in each `##` section. Do not link inside headings.
- **See also** is a bulleted list of `[[Title]]` links, chosen by hand. It must obey the Union quarantine (structure doc 7.1).
- **Inside a Markdown table, links never use the `|text` form**, because the pipe would split the table cell. Use `[[Title]]` or `[[Title#Heading]]` only.

### 5.4 Hatnotes

When a section summarises a topic that has its own article, the first line under the heading is a hatnote in exactly this form:

```markdown
## The census, 4 BBY

*Main article: [[The Census of 4 BBY]]*
```

### 5.5 Text conventions

- **Masterdoc sentences stay as written (authors' rule, 15 October 2026).** An article reuses the masterdoc's sentences with the same wording, length and structure. Never split, shorten, merge or reword a masterdoc sentence for style. Change one only when the article's structure requires it:
  - a pronoun, "also" or "the latter" that points at text the article does not carry
  - an author correction
  - a sentence of which only part belongs in the article

  Make the smallest change that works, and keep the rest verbatim. If unsure about a sentence, ask the authors. `WORKFILES/tools/sentence_check.py` flags masterdoc sentences that an article has split or reworded.
- **Slips and spelling:** obvious slips in the masterdoc are fixed, and American spellings are made British, wherever a sentence is carried. Both lists are in `WORKFILES/author-corrections.md`. A new slip goes to the authors before it is fixed.
- **The general "you" stays.** The masterdoc's "you" in turns of phrase, such as "the benevolent authority that does not come for you", is general. It does not address the reader, so it is carried as written.
- **The brief's sentence-length rules do not apply to articles.** These are the average of nine words, almost nothing over twenty, and one joining word. They were for writing the masterdoc.
- **New text follows the masterdoc's own voice.** This covers what an article has to add itself: the lead, the Background, and a linking sentence where a passage needs one.
  - the historical register, never addressing the reader
  - dry understatement
  - British spelling, and "magick"
- **No em dashes anywhere, including the front matter.** En dashes are used only in ranges (`19–15 BBY`).
- **Closing sentences:** when an article retells a masterdoc passage, it keeps that passage's closing sentence. Those sentences carry the weight.
- **Keep the hedges:** compression must never drop the masterdoc's qualifiers, such as "supposedly", "about", "almost certainly", "nothing has ever been proved" or a named exception. Several of them guard deliberate ambiguities.
- **Check inferred dates:** a year worked out from a relative date ("three months before Yavin", "at nineteen") must agree with the ages and dates elsewhere in the masterdoc.
- **Nothing beyond the sources:** the cited passages and, in Background only, the canon notes. Nothing else. Where `WORKFILES/author-corrections.md` corrects the masterdoc, the correction wins.
- **Tense:** past for events, present for the state of things at the end of 2 ABY.
- **Numbers and dates** in prose are written as the masterdoc writes them, usually in words: "eleven thousand four hundred", "the fourth month of 1 ABY".
- **Quotations** are verbatim from the masterdoc, in double quotes. A quotation of more than two sentences goes in a `>` block quote.
- **Bold** is used only for the subject's first mention in the lead.
- **Italics** are used only for hatnotes.

### 5.6 Images in the body

An article with more images than its infobox image carries the others in the body, as **image blocks** (authors' decision, 31 October 2026). An image block is a fenced block with the info string `image`. It holds the same four keys as the infobox, in the same order and with the same rules (4):

````markdown
```image
image: "the-republic-corps-marshal.jpg"
image_caption: ""
artwork_author: "MandaloArt"
artwork_author_link: "https://www.instagram.com/mandalo_art"
```
````

- **Keys:** all four are present, in this order, and nothing else goes in the block. `image` is required. The other three may be `""`, as in the infobox.
- **Placement:** a block sits between two sections. It comes after the last paragraph of one section and before the next `##` or `###` heading, with a blank line on each side.
- **Where a block never goes:**
  - in the lead
  - directly under a heading, where a hatnote may stand
  - inside a paragraph or a list
  - in or after `## See also`
- **Spacing:** the blocks are spread evenly through the article. Where a section is about the image's subject, the block closes that section.
- **Rendering:** the website draws each block as a figure beside the text, with its caption and the artist's credit. The block is not prose. The lint and the sentence check skip it.

---

## 6. Reading aids (`pages/`)

Main Page, Timeline, Glossary, Canon and sources and The History use the same front matter with `category: page`, `tier: none`, and no `tags` or infobox. Their bodies are free in form but follow the text conventions in 5.5.

**The History** (authors' instruction, 24 October 2026) is the masterdoc as one page, with every correction applied. Chapter XIV, the biographical register, is left out, because each figure in it has an article (the authors, 24 October 2026). Its form:
- The lead names the history and its authors. `## Preface` holds the preface and the canon list.
- Each chapter is a `##` section headed by its numeral and title, for example `## X. The Battle of Yavin`. Each masterdoc section is a `###` subsection under its own heading.
- A "Main article" hatnote (5.4) sits under each chapter or section that an article covers. Chapter XV has no hatnote. The chapters keep the masterdoc's numerals, so XIII is followed by XV, and the lead says why.
- The text has no other links. Italics and bold are dropped, except the lead's title, and lists are plain.
- The canon list's capitalised heading is in sentence case. The masterdoc's two hard line breaks become paragraph breaks, as in the approved articles: in the preface before "A new galactic epoch…", and in X.4 before "Anakin Skywalker, disgraced…".
- The page is built by `WORKFILES/tools/build_history.py`, which applies the corrections and lists every changed sentence in `WORKFILES/reviews/the-history-changes.md`. Once the authors have edited the page, it is not rebuilt.
- It carries every Union allusion where the masterdoc puts them, so the lint exempts it from the quarantine (structure doc 7.1), except "dreadnought", and from the Grand Master link rule (7.3).
