# Brief: building the Low Republic wiki website

This project builds the website for **The Low Republic**, a Star Wars alternate-universe setting for tabletop play. All the content is finished: 115 articles and 5 pages, written as Markdown files with YAML front matter. **This project is only the code side:** reading those files, interpreting their format and turning them into a working wiki. The writing is done and is not this project's concern. Treat the article files as read-only source content; the authors edit them by hand, and the site must pick up their edits.

## The source files

- **Location:** the `ARTICLES/` folder (from `D:\Tabletop RPGs\lowrepublic\WIKIARTICLESPROJECT\ARTICLES`). **`ARTICLES/_FORMAT.md` is the full format specification and the authority whenever this brief and it differ.** Read it first.
- **Folders:**

  | Folder | Category | Count |
  |---|---|---|
  | `history/` | `history` | 10 |
  | `factions/` | `faction` | 19 |
  | `characters/` | `character` | 65 |
  | `places/` | `place` | 21 |
  | `pages/` | `page` | 5 |

  The artwork is in `ARTWORKS/`, a separate flat folder beside `ARTICLES/` (JPG, PNG, WebP and SVG). Image fields give the file name only, never a folder.
- **Files to skip:** any file whose name begins with `_` is documentation.
- **File names:** each file name is the slug of the title. Lowercase it, strip accents, remove apostrophes and full stops, and turn spaces into hyphens (`Padmé Amidala` becomes `padme-amidala.md`, `Do'Kass` becomes `dokass.md`). The files are UTF-8, and titles and headings contain accents, apostrophes, commas and en dashes (`The schism, 14–8 BBY`).

## Front matter

Each file opens with a YAML block between `---` lines. It is a deliberately small subset of YAML and is valid for any standard parser:
- one `key: value` per line
- inline lists `[a, b]`
- double-quoted strings
- nesting only under `tags` and `infobox`, two spaces deep

**Top-level keys, in order:**

| Key | Meaning |
|---|---|
| `title` | The display title and the name links use. |
| `category` | `history`, `faction`, `character`, `place` or `page`. |
| `tier` | `hub`, `major`, `standard`, `short`, `stub`, or `none` for pages. This indicates size and importance; use it for layout or listings if useful. |
| `batch` | Writing workflow metadata; it can be ignored. |
| `status` | `draft`, `reviewed` or `approved`. All are `approved` now. |
| `sources` | Codes for the passages of the setting's history that the article draws on. The site builds an "In the history" box from them (see below). The body never lists them itself. |
| `canon` | `true` if the article has a `## Background` section of material from the original Star Wars canon. The site may style or label that section. |
| `tags` | `affiliation`, `period` and `region` lists, from fixed vocabularies (_FORMAT 3.4). Use them for category pages and filters. Pages have no tags. |
| `redirects` | Other names that should lead to this article. A plain name goes to the top. `Name#Heading` sends that name to a section of this article. |
| `infobox` | The infobox, drawn at the top right of the page. Absent on all pages and on the two composite articles, Galactic regions and Three Stances of the Senate. |

## Infoboxes

- **Image keys:** every infobox starts with `image`, `image_caption`, `artwork_author` and `artwork_author_link`, and any of them may be an empty string.
  - `image` is a file name in `ARTWORKS/`, such as `maul.jpg`. 42 articles have one.
  - Credit the artist from the other two keys, linking the name when `artwork_author_link` (a URL) is set.
  - Some images have an author and no link, such as the Star Wars logos credited to "Lucasfilm and Disney". Ilai Vess's image has neither.
  - The authors are still writing the captions.
- **Value types:** values are short text or lists. List fields are always lists, even with one item. Text values and list items can contain wiki-links, which need rendering.
- **Missing values:** a key with no value is simply absent, so render only what is there.
- **Labels:** the site needs display labels for the keys, such as `senate_stance` "Senate stance", `schism_camp` "Schism camp" and `also_known_as` "Also known as".
- **Keys in use:**

  | Category | Keys |
  |---|---|
  | Character | `name`, `also_known_as`, `designation`, `species`, `model`, `homeworld`, `born`, `died`, `affiliation`, `position`, `formerly`, `senate_stance`, `schism_camp` |
  | Faction | `type`, `also_known_as`, `founded`, `founder`, `leader`, `seat`, `territory`, `strength`, `affiliated_with`, `predecessor`, `status` |
  | History | `type`, `date`, `place`, `participants`, `key_figures`, `drafted_by`, `carried_by`, `result`, `losses`, `preceded_by`, `followed_by` |
  | Place | `type`, `also_known_as`, `region`, `sector`, `held_by`, `population`, `locations` |

  Mandalore is filed under factions but uses the place infobox plus some faction keys, so render whatever keys are present.
- **`born`:** a display string, such as `46 BBY (aged 48)`, `32 BBY (physically 68)` or `Age unrecorded`.
- **The history chain:** `preceded_by` and `followed_by` on history articles are lists of links that form a branching chronological chain (_FORMAT 4.3.1). Show them as previous and next navigation. An article can lead into several threads at once.

## Body

- **The lead** is the text before the first heading. The subject's name is in **bold** at its first appearance. Bold is used for nothing else.
- **Headings:** there is no `#` heading in the body, because the title comes from the front matter. `##` marks sections and `###` subsections, and nothing deeper is used. Headings are link targets, so every heading needs a stable anchor. Other articles link to them by their exact text, en dashes and commas included.
- **Section order:** lead, then `## Background` where `canon: true`, then the content sections, then usually `## In 2 ABY`, which is the present state of things. `## See also` comes last and is a plain bulleted list of links.
- **Hatnotes:** a line in exactly the form `*Main article: [[Title]]*` or `*Main article: [[Title#Heading]]*`, directly under a heading. Render it as a hatnote, not as ordinary italics. Italics are used for nothing else.
- **Image blocks** (_FORMAT 5.6): extra images in the body, as a fenced block with the info string `image`. It holds the same four keys as the infobox, in YAML form:

  ````markdown
  ```image
  image: "the-republic-corps-marshal.jpg"
  image_caption: ""
  artwork_author: "MandaloArt"
  artwork_author_link: "https://www.instagram.com/mandalo_art"
  ```
  ````

  - A block always sits between sections, just before a heading. Render it as a figure beside the text, with caption and credit, never as code.
  - Four articles use blocks now: The Grand Union Army, The Republic Corps (two blocks), The Shadow Collective and The Shadow Troopers.
- **Other Markdown:**
  - paragraphs
  - bullet lists
  - `>` block quotes, on the pages
  - tables, on the pages only
  - British spelling, single quotes kept as written
  - no em dashes anywhere

## Wiki-links

| Form | Meaning |
|---|---|
| `[[Title]]` | A link to the article with that exact title. |
| `[[Title\|text]]` | The same link, showing `text`. |
| `[[Title#Heading]]` | A link to a section, by its exact heading text. |
| `[[Title#Heading\|text]]` | The same section link, showing `text`. |

- Links always use real titles, never redirect names. Figures without an article are linked through the article that covers them, as in `[[The Death of Palpatine|Palpatine]]`.
- Inside Markdown tables, links never use the `|text` form.
- About a hundred distinct section links are in use. `WORKFILES/manifest.md`, "Planned link targets", lists the main ones. The site should report any link whose title or heading does not resolve.

## The "In the history" box and The History page

- **What the codes refer to:** the `sources` codes point into the setting's history, which the page `pages/the-history.md` (title "The History") carries in full.
  - `Pref` is its `## Preface`.
  - A roman numeral alone, such as `XV`, is the whole chapter, headed `## XV. …`.
  - `XI.2` is chapter XI, section 2: the second `###` heading under `## XI. …`.
  - `R:Title` is the subject's entry in the biographical register (the history's Chapter XIV). That chapter is left out of The History, because each figure in it has an article, so link an `R:` code to the article with that title. Ki-Adi-Mundi and Stass Allie share one entry.
- **Building the box:** the site can build each article's "In the history" box by mapping these codes to anchors on The History.
- **The History page:** it is long, with chapters as `##` and sections as `###`. It needs a table of contents.

## Pages

There are five pages: Main Page (the front page), Timeline, Glossary, Canon and sources, and The History. They have `category: page` and `tier: none`, and no tags or infobox. Their bodies are free in form, with tables, lists and block quotes.

## Two rules the site must enforce

### A hidden article

**Vesk Tolloran** (`characters/vesk-tolloran.md`) is meant to be found only by readers who already know his name. No other article links to him or names him, and the site must not reveal him either. Keep him out of:
- every list and index, such as category pages, tag pages, "all characters", "random article" and "recently added"
- automatic suggestions and related articles
- the backlinks ("what links here") of the pages his article links to

He must still be reachable by search, by his title or his redirect names, and by a direct URL.

### No automatic links between the Union articles

**No automatic "related articles" between these eight articles:**
- Orson Krennic
- The Republic Remade
- The Secessions
- The Greater Seswenna Union
- Dedra Meero
- Thrawn
- Deran Kolt
- Eriadu

They each hold one piece of a secret that the setting keeps scattered on purpose. Any automatic feature that groups or suggests articles (related articles, "more like this", tag-based suggestions, generated see-also lists) must never join two of them. Hand-written links in the text are fine as they are. The History page is exempt, since it carries the whole history.

## Validation tool

The writing project has a validator, `WORKFILES/tools/lint.py`, in `D:\Tabletop RPGs\lowrepublic\WIKIARTICLESPROJECT`. It checks front matter, keys, tags and links against the format, and it shows one way to parse these files.

## Left to this project

These are all yours to decide, as long as the format above is read faithfully and the article files are never rewritten by the build:
- the stack and site generator
- the URL scheme
- styling, search and how redirects are served
- whether drafts are hidden
