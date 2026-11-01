# The Low Republic wiki: guide for the authors

The wiki at **https://thelowrepublic.github.io/** is built automatically from this repository. You keep writing articles as before, and the site rebuilds itself every time something changes on `main`. You never need to touch the code to keep the wiki up to date.

This guide covers how edits go live, what the build's messages mean, how to add articles and pictures, every setting you can change, and what to do if something goes wrong.

---

## In short

- **Edit or upload files on `main`** (articles in `ARTICLES/`, pictures in `ARTWORKS/`). The live site updates about **a minute and a half** later.
- **Watch progress on the repository's Actions tab.** A green tick means the new version is live. A red cross means nothing was published and the previous version is still online; the run's page says why.
- **Settings live in one file:** `WIKI-SITE/config.yml`.
- **The design and every decision behind it** are recorded in `WIKI-SITE/GAMEPLAN.md`.

---

## How an edit goes live

1. Change something on `main`: upload files with **Add file → Upload files**, edit a file in the browser and commit it, or push from your computer.
2. GitHub starts the workflow **Build and publish the wiki**. It:
   1. installs what the build needs,
   2. builds the site from `ARTICLES/` and `ARTWORKS/`,
   3. checks the site's rules (see below),
   4. runs the tests,
   5. publishes the result.
3. Open the **Actions** tab to watch it. Clicking a run shows a summary: how many pages were built, any warnings, and a table of the rule checks.

If the site does not look changed afterwards, your browser may be showing a stored copy: press **Ctrl+F5** (Windows) or **Cmd+Shift+R** (Mac).

---

## What the results mean

| You see | It means | What happens |
|---|---|---|
| Green tick, no notes | All good | The new version is live. |
| Green tick with **warnings** (yellow) | Something in the articles needs your attention | The new version is **still published**. |
| Red cross | The build failed, a rule was broken, or a test failed | **Nothing is published.** The previous version stays online until it is fixed. |

**Warnings** are things only the authors can decide, for example:

- a `[[link]]` to a title no article has: the page shows it as a red link
- a `[[Title#Heading]]` link to a heading the article does not have: it leads to the top of the article instead
- an image named in an article that is not in `ARTWORKS/`
- a `sources` code that matches no section of The Entire History

**A red cross** happens when:

- **an article's front matter cannot be read.** The run's **Build the site** step says `BUILD FAILED` and names the file and line. The usual causes: a value containing `:` or `#` without quotes, a tab instead of spaces, or a missing closing `---`.
- **a rule check fails.** The **Check the site's rules** step names the rule and the page. The rules are listed below.
- **a test fails.** This normally only happens after a change to the site's code.

---

## Articles

`ARTICLES/_FORMAT.md` is the authority on how articles are written. The site reads it as written; anything that follows the format works.

- **A new article:** create the `.md` file in the folder for its category (`characters/`, `factions/`, `history/`, `places/` or `pages/`). Name the file after the title's slug: lowercase, no accents, no apostrophes or full stops, spaces become hyphens (`Padmé Amidala` → `padme-amidala.md`). It then appears everywhere by itself: its own page, its category page, search, random article, its redirects. Link to it from other articles with `[[Its Title]]`.
- **Renaming an article:** change the `title` and the file name, then fix the links to it. Every link still using the old title shows up as a warning. Add the old title to the article's `redirects`, so old addresses and searches still lead to it.
- **Redirects** (`redirects:` in the front matter) become search names and addresses: `/wiki/darth-sidious/` opens The Death of Palpatine and says "Redirected from Darth Sidious". `Name#Heading` leads to that section.
- **Sources** (`sources:`) become the "In the history" box at the foot of the article, linking to each section of The Entire History.

### Pictures in articles

- Put the file in `ARTWORKS/` and name it in the infobox's `image:` or in an image block (`_FORMAT.md` section 5.6). JPG, PNG, WebP and SVG all work. The site makes smaller copies for the page and links the original.
- **Credits:** each picture shows "Artwork by *artist*", linked to `artwork_author_link`.
  - If `artwork_author` is empty, it says **"Artwork by Lucasfilm and Disney"** (the setting `default_artwork_author`).
  - For a picture whose artist is genuinely unknown, add the file name to `unknown_artist_images`; it then says "Artwork by unknown artist".
- **Where an image block appears:** a block shows beside the text of the section it closes, meaning the section just before it in the file. To show it beside a different section, move the block to the end of that section.
- **The Art credits page** lists every artist and the articles their work appears in, automatically.

### The two special rules

Both are enforced on every publish:

- **Hidden articles** (`hidden` in the settings; today Vesk Tolloran) appear in no list, random article or sitemap, and no page links to them or names them, except their own page and their own category page (Vesk is listed under Characters; the setting `hidden_on_category_pages` turns this off). They can still be found by search, by their redirect names and by their address.
- **The Union quarantine** (`quarantine` in the settings): nothing the site generates by itself, such as the "In the history" box, ever links one of these eight articles to another. Links you write in the text are left as they are. The Art credits page may list them side by side.

---

## The Main Page extras and site pictures

These files sit in the main folder of the repository. Replace a file with one of the same name and the site uses the new one on the next publish.

| File | Used for | Setting |
|---|---|---|
| `lowrepubliclogowide.png`, `lowrepubliclogotall.png` | the logo in the top bar, and on the Main Page and disclaimer | none |
| `lowrepublicicon.png` | the browser-tab and phone home-screen icons (square, 512 px) | `icon` |
| `lowrepublicmap.jpg` | the map at the end of the Main Page | `main_page: map:` |
| `WIKI-SITE/assets/social-card.png` | the picture shown when a page without artwork is shared on Discord or social media (1200 × 630 px) | `social_image` |

When a page is shared, the preview shows the article's own artwork if it has a JPG, PNG or WebP image, and the card otherwise. The text under it is the article's first sentence.

---

## Settings: `WIKI-SITE/config.yml`

Edit it on GitHub like any other file. Indent with spaces (never tabs), and put quotes around a value that contains `:` or `#`.

| Setting | What it does |
|---|---|
| `site_name` | The name in browser tabs and link previews. |
| `site_url` | The site's full address, for link previews and the sitemap. Change it only if the address changes (for example a custom domain). |
| `site_path` | The path the site is served from: `/` for the current address. |
| `social_image` | The default link-preview picture. |
| `footer` | The text at the foot of every page. |
| `sidebar_links` | The links at the top of the sidebar, in order (article titles). "Random article" is always added after them. |
| `categories` | The sidebar's Browse links and the category pages' names. |
| `history_page` | The page that holds the whole history (The Entire History); `sources` codes point into it. |
| `search_exclude` | Articles left out of search entirely (today The Entire History). |
| `notices` | Boxes above an article's first paragraph, such as the "Before you read" box on The Entire History. Text may use `[[links]]`. |
| `hidden` | Hidden articles (see the two special rules). |
| `hidden_on_category_pages` | `true` lists hidden articles on their own category page (today Vesk on Characters); `false` leaves them off it too. |
| `quarantine` | The Union quarantine's eight articles. |
| `labels` | The names shown in infoboxes for each key (`senate_stance` → "Senate stance"). A pair gives the singular and plural. |
| `canon_link` | Where the "Canon" tag beside a Background heading leads. |
| `art_credits` | The contact link at the end of the Art credits page (today your Discord profile). |
| `default_artwork_author` | The credit for pictures with no `artwork_author`. |
| `unknown_artist_images`, `unknown_artist_label` | Pictures by an unknown artist, and how they are credited. |
| `disclaimer` | The notice visitors acknowledge before entering. After changing its text, **raise `version` by one**, so visitors who already acknowledged it see the new text. `show_on: all` shows it on whichever page a new visitor opens first; `main` only on the Main Page. |
| `icon` | The browser-tab icon file. |
| `page_transition` | The animation when a reader follows a link to another page: `record` (every line of text types itself out at once) or `none`. |
| `page_transition_seconds` | How long that animation takes, in seconds (today 0.8). |
| `main_page` | The Main Page map. |

---

## Changing the look

- **Colours** are set once at the top of `WIKI-SITE/static/style.css`: `--detail` is the Tatooine sand of the infobox bands and lines, `--link` the link blue, `--bg` the background, `--text` the text.
- **Fonts:** Orbitron for headings and Barlow for text, stored in `WIKI-SITE/static/fonts/`. The variables `--heading` and `--sans` in `style.css` choose them.
- **Page layouts** are the files in `WIKI-SITE/templates/`.

These are code. If you change them, the next publish shows straight away whether anything broke.

### The page animation

When a reader follows a link to another page of the wiki, every line of text on the new page types itself out at the same moment, left to right, in 0.8 seconds (settings `page_transition` and `page_transition_seconds`). It does not play for visitors arriving from outside the wiki, on back/forward or reload, for a link to a section, or when the reader's device is set to reduce motion.

Readers can turn it off with the small switch to the right of the search box (on phones, at the end of the logo row). A brief pop-up confirms "Site animations on" or "off", and the browser remembers the choice. Setting `page_transition: none` removes the animation and the switch for everyone.

---

## Previewing on your own computer (optional)

You do not need this: every publish checks everything. It helps if you want to see a change before it goes live, and it needs a copy of the repository on your computer (for example through GitHub Desktop).

1. Install **Python 3.12 or newer** from python.org. On Windows, tick **"Add python.exe to PATH"** during installation.
2. Open a terminal in the repository's folder (the one containing `ARTICLES` and `WIKI-SITE`).
3. Once, install what the build needs:

   ```
   pip install -r WIKI-SITE/requirements.txt
   ```

4. Build the site:

   ```
   python WIKI-SITE/build.py
   ```

5. Serve it:

   ```
   python -m http.server 8000 -d WIKI-SITE/_site
   ```

6. Open **http://localhost:8000** in your browser. Rebuild (step 4) after each change and refresh the page.

To run the same checks and tests as GitHub:

```
python WIKI-SITE/tests/check_site.py
python -m unittest discover -s WIKI-SITE/tests -t WIKI-SITE/tests
```

The built site in `WIKI-SITE/_site/` is never committed; GitHub builds its own copy.

---

## What is in this folder

| Path | What it is |
|---|---|
| `README.md` | This guide. |
| `GAMEPLAN.md` | The plan, the design and every decision made with the authors. |
| `config.yml` | The settings. |
| `build.py` | The program that turns the articles into the website. |
| `templates/` | The page layouts. |
| `static/` | The stylesheet, scripts and fonts. |
| `assets/` | The default link-preview card. |
| `tests/` | `check_site.py` (the rule checks) and the tests. |
| `analysis/` | The first survey of the articles. |
| `requirements.txt` | The Python packages the build uses. |
| `../.github/workflows/pages.yml` | The GitHub workflow that builds and publishes the site. |

---

## Troubleshooting

- **The site did not change.** Look at the Actions tab: is the run still going, or did it fail? Then refresh with Ctrl+F5.
- **`BUILD FAILED`.** Open the run, then the **Build the site** step. The message names the article and the problem, usually its front matter. Fix the file on `main` and the site rebuilds by itself.
- **A rule check failed.** The **Check the site's rules** step lists the rule and the page, for example "names the hidden article". Remove the offending link or name.
- **A link shows in red.** Its title does not match any article exactly: check the spelling, accents and capitals against the article's `title`.
- **Visitors do not see a changed disclaimer.** Raise `disclaimer: version:` in the settings.
