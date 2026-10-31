"""Survey of the ARTICLES/ folder.

Reads every article the way the future site build will, and reports what the
build has to handle: front-matter shapes, infobox keys, images, wiki-links,
section anchors, redirects, source codes and the Markdown features in use.

Run from the repository root:  python3 WIKI-SITE/analysis/survey.py
It only reads; it never writes to ARTICLES/ or ARTWORKS/.
"""

import collections
import os
import re
import sys
import unicodedata

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTICLES = os.path.join(ROOT, "ARTICLES")
ARTWORKS = os.path.join(ROOT, "ARTWORKS")

LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\\?\|([^\]]+))?\]\]")
FENCE_RE = re.compile(r"^```(\w*)\s*$")
HATNOTE_RE = re.compile(r"^\*Main article: (.+)\*$")


def slug(text):
    """The file-name slug rule from _FORMAT 1."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("'", "").replace("’", "").replace(".", "")
    return text.replace(" ", "-")


def anchor(heading):
    """A stable, URL-safe anchor for a heading (proposed site rule)."""
    text = unicodedata.normalize("NFKD", heading)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = text.replace("–", "-").replace("'", "").replace("’", "")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def load(path):
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    if not raw.startswith("---\n"):
        raise ValueError("no front matter")
    _, fm, body = raw.split("---\n", 2)
    return yaml.safe_load(fm), body, fm


def walk_values(value):
    if isinstance(value, list):
        for v in value:
            yield from walk_values(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from walk_values(v)
    else:
        yield value


def main():
    articles = {}
    problems = []
    for folder in sorted(os.listdir(ARTICLES)):
        fpath = os.path.join(ARTICLES, folder)
        if not os.path.isdir(fpath):
            continue
        for name in sorted(os.listdir(fpath)):
            if name.startswith("_") or not name.endswith(".md"):
                continue
            path = os.path.join(fpath, name)
            try:
                meta, body, fm_raw = load(path)
            except Exception as exc:  # noqa: BLE001
                problems.append(f"PARSE {folder}/{name}: {exc}")
                continue
            articles[meta["title"]] = dict(
                meta=meta, body=body, fm_raw=fm_raw, folder=folder, file=name
            )

    print(f"# Survey of ARTICLES/  ({len(articles)} articles and pages parsed)\n")

    # ---- counts ----------------------------------------------------------
    by_cat = collections.Counter(a["meta"]["category"] for a in articles.values())
    by_tier = collections.Counter(a["meta"]["tier"] for a in articles.values())
    by_status = collections.Counter(a["meta"]["status"] for a in articles.values())
    print("## Counts\n")
    print("- category:", dict(by_cat))
    print("- tier:", dict(by_tier))
    print("- status:", dict(by_status))
    not_approved = [t for t, a in articles.items() if a["meta"]["status"] != "approved"]
    print("- not approved:", not_approved)

    # ---- file name / folder checks ----------------------------------------
    folder_for = dict(character="characters", faction="factions", history="history",
                      place="places", page="pages")
    for t, a in articles.items():
        if slug(t) + ".md" != a["file"]:
            problems.append(f"SLUG {a['folder']}/{a['file']}: title '{t}' slugs to {slug(t)}.md")
        if folder_for[a["meta"]["category"]] != a["folder"]:
            problems.append(f"FOLDER {a['file']}: category {a['meta']['category']} in {a['folder']}/")

    # ---- YAML type surprises ----------------------------------------------
    print("\n## Non-string scalar values in front matter (YAML type coercion)\n")
    for t, a in articles.items():
        for key, val in a["meta"].items():
            if key in ("tags", "infobox", "sources", "redirects"):
                vals = list(walk_values(val))
            else:
                vals = [val]
            for v in vals:
                if not isinstance(v, str) and key not in ("batch", "canon"):
                    print(f"- {t}: {key} -> {v!r} ({type(v).__name__})")

    # ---- infoboxes --------------------------------------------------------
    print("\n## Infobox keys by category\n")
    keys_by_cat = collections.defaultdict(collections.Counter)
    no_infobox = []
    for t, a in articles.items():
        ib = a["meta"].get("infobox")
        if ib is None:
            no_infobox.append(t)
            continue
        for k in ib:
            keys_by_cat[a["meta"]["category"]][k] += 1
    for cat, ctr in keys_by_cat.items():
        print(f"- **{cat}**: " + ", ".join(f"{k} ({n})" for k, n in ctr.items()))
    print(f"- no infobox: {[t for t in no_infobox if articles[t]['meta']['category'] != 'page']} + all pages")

    list_valued = collections.Counter()
    for a in articles.values():
        for k, v in (a["meta"].get("infobox") or {}).items():
            if isinstance(v, list):
                list_valued[k] += 1
    print("- keys that hold lists:", sorted(list_valued))
    longest = sorted(
        ((len(str(v)), t, k) for t, a in articles.items()
         for k, v in (a["meta"].get("infobox") or {}).items() if not k.startswith(("image", "artwork"))),
        reverse=True)[:5]
    print("- longest infobox values:", [(t, k, n) for n, t, k in longest])

    # ---- images -------------------------------------------------------------
    print("\n## Images\n")
    art_files = set(os.listdir(ARTWORKS)) - {"art_credits_links.txt"}
    used = set()
    blocks = []
    captions = 0
    for t, a in articles.items():
        ib = a["meta"].get("infobox") or {}
        if ib.get("image"):
            used.add(ib["image"])
            if ib["image"] not in art_files:
                problems.append(f"IMAGE missing: {t} infobox -> {ib['image']}")
            if ib.get("image_caption"):
                captions += 1
        # body image blocks
        lines = a["body"].split("\n")
        i = 0
        while i < len(lines):
            m = FENCE_RE.match(lines[i])
            if m:
                j = i + 1
                while j < len(lines) and not lines[j].startswith("```"):
                    j += 1
                info = m.group(1)
                if info == "image":
                    data = yaml.safe_load("\n".join(lines[i + 1:j]))
                    blocks.append((t, data))
                    used.add(data["image"])
                    if data["image"] not in art_files:
                        problems.append(f"IMAGE missing: {t} block -> {data['image']}")
                    nxt = next((l for l in lines[j + 1:] if l.strip()), "")
                    if not nxt.startswith("#"):
                        problems.append(f"IMAGE block not before a heading: {t}")
                else:
                    problems.append(f"FENCE with info '{info}' in {t}")
                i = j
            i += 1
    infobox_imgs = sum(1 for a in articles.values() if (a["meta"].get("infobox") or {}).get("image"))
    print(f"- infobox images: {infobox_imgs}; filled captions: {captions}")
    print(f"- body image blocks: {len(blocks)} in {sorted(set(t for t, _ in blocks))}")
    print(f"- artwork files not used by any article: {sorted(art_files - used)}")
    ext = collections.Counter(os.path.splitext(f)[1] for f in art_files)
    print(f"- formats: {dict(ext)}")
    no_author = [t for t, a in articles.items()
                 if (a["meta"].get("infobox") or {}).get("image")
                 and not a["meta"]["infobox"].get("artwork_author")]
    no_link = [t for t, a in articles.items()
               if (a["meta"].get("infobox") or {}).get("artwork_author")
               and not a["meta"]["infobox"].get("artwork_author_link")]
    print(f"- image with no artist: {no_author}; artist with no link: {no_link}")

    # ---- headings / anchors -------------------------------------------------
    headings = {}
    for t, a in articles.items():
        hs = []
        for line in a["body"].split("\n"):
            m = re.match(r"^(#{1,6}) (.+?)\s*$", line)
            if m:
                level = len(m.group(1))
                if level == 1 or level > 3:
                    problems.append(f"HEADING level {level} in {t}: {line}")
                hs.append(m.group(2))
        headings[t] = hs
        anchors = collections.Counter(anchor(h) for h in hs)
        for an, n in anchors.items():
            if n > 1:
                problems.append(f"ANCHOR collision in {t}: '{an}' x{n}")

    # ---- links --------------------------------------------------------------
    print("\n## Wiki-links\n")
    total = 0
    section_links = set()
    backlinks = collections.defaultdict(set)
    for t, a in articles.items():
        text = a["body"] + "\n" + a["fm_raw"]
        for m in LINK_RE.finditer(text):
            total += 1
            target, head, _ = m.groups()
            if target not in articles:
                problems.append(f"LINK unresolved title in {t}: [[{m.group(0)[2:-2]}]]")
                continue
            backlinks[target].add(t)
            if head:
                section_links.add((target, head))
                if head not in headings[target]:
                    problems.append(f"LINK unresolved heading in {t}: [[{target}#{head}]]")
    print(f"- {total} links, {len(section_links)} distinct section links")
    print(f"- articles nobody links to: {sorted(t for t in articles if t not in backlinks)}")
    print(f"- who links to Vesk Tolloran: {sorted(backlinks.get('Vesk Tolloran', []))}")
    # Union quarantine: hand-written links between the eight are allowed; just report them
    union = {"Orson Krennic", "The Republic Remade", "The Secessions", "The Greater Seswenna Union",
             "Dedra Meero", "Thrawn", "Deran Kolt", "Eriadu"}
    shared_tags = collections.Counter()
    for x in union:
        for y in union:
            if x < y:
                tx, ty = articles[x]["meta"].get("tags", {}), articles[y]["meta"].get("tags", {})
                common = set(tx.get("affiliation", [])) & set(ty.get("affiliation", []))
                if common:
                    shared_tags[f"{x} / {y}"] = len(common)
    print(f"- Union-quarantine pairs sharing an affiliation tag (a naive 'related' feature would join them): {len(shared_tags)} of 28")

    # ---- redirects ----------------------------------------------------------
    print("\n## Redirects\n")
    seen = {}
    n_red = 0
    for t, a in articles.items():
        for r in a["meta"].get("redirects") or []:
            n_red += 1
            name, _, head = r.partition("#")
            if head and head not in headings[t]:
                problems.append(f"REDIRECT heading missing: {t} <- {r}")
            key = name.lower()
            if key in (x.lower() for x in articles):
                problems.append(f"REDIRECT name equals a title: {t} <- {name}")
            if key in seen and seen[key] != t:
                problems.append(f"REDIRECT clash: '{name}' -> {seen[key]} and {t}")
            seen[key] = t
    print(f"- {n_red} redirect names on {sum(1 for a in articles.values() if a['meta'].get('redirects'))} articles")

    # ---- sources ------------------------------------------------------------
    print("\n## Source codes -> The History anchors\n")
    hist = articles["The History"]["body"].split("\n")
    chapters = {}
    current = None
    for line in hist:
        m = re.match(r"^## ([IVXL]+)\. (.+)$", line)
        if m:
            current = m.group(1)
            chapters[current] = [m.group(0)[3:]]
        elif line.startswith("### ") and current:
            chapters[current].append(line[4:])
    print(f"- chapters on The History: {list(chapters)}")
    bad = collections.Counter()
    codes = collections.Counter()
    for t, a in articles.items():
        for code in a["meta"].get("sources") or []:
            code = str(code)
            if code.startswith("R:"):
                codes["R:"] += 1
                if code[2:] not in articles:
                    bad[f"{code} (in {t})"] += 1
                continue
            if code == "Pref":
                codes["Pref"] += 1
                continue
            chap, _, sec = code.partition(".")
            codes["chapter" if not sec else "section"] += 1
            if chap not in chapters:
                bad[f"{code} (in {t})"] += 1
            elif sec and int(sec) > len(chapters[chap]) - 1:
                bad[f"{code} (in {t})"] += 1
    print(f"- code kinds: {dict(codes)}")
    print(f"- codes that do not resolve: {sorted(bad)}")

    # ---- markdown features ----------------------------------------------------
    print("\n## Markdown features used in bodies\n")
    feats = collections.defaultdict(set)
    for t, a in articles.items():
        in_fence = False
        for line in a["body"].split("\n"):
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            s = line.rstrip()
            if s.startswith("|"):
                feats["table"].add(t)
            if s.startswith(">"):
                feats["blockquote"].add(t)
            if re.match(r"^\d+\. ", s):
                feats["ordered list"].add(t)
            if re.match(r"^\s+[-*] ", s):
                feats["nested list"].add(t)
            if re.match(r"^- ", s):
                feats["bullet list"].add(t)
            if HATNOTE_RE.match(s):
                feats["hatnote"].add(t)
            elif re.search(r"(?<!\*)\*[^*\s][^*]*\*(?!\*)", s) or re.search(r"(?<!_)_[^_\s][^_]*_(?!_)", s):
                feats["italics outside hatnote"].add(t)
            if "<" in s and re.search(r"<[a-zA-Z/]", s):
                feats["raw HTML"].add(t)
            if re.match(r"^(-{3,}|\*{3,})$", s):
                feats["horizontal rule"].add(t)
            if "—" in s:
                feats["em dash"].add(t)
            if re.search(r"\[[^\[\]]+\]\(", s):
                feats["markdown link [x](y)"].add(t)
            if re.search(r"  $", line):
                feats["trailing double space (hard break)"].add(t)
        bolds = re.findall(r"\*\*([^*]+)\*\*", a["body"])
        if len(bolds) > 1:
            feats["bold more than once"].add(t)
        if not bolds and a["meta"]["category"] != "page":
            feats["no bold in lead"].add(t)
    for f, ts in sorted(feats.items()):
        shown = sorted(ts) if len(ts) <= 8 else f"{len(ts)} articles"
        print(f"- {f}: {shown}")

    # ---- size ----------------------------------------------------------------
    words = sorted(((len(a["body"].split()), t) for t, a in articles.items()), reverse=True)
    print(f"\n## Size\n\n- total words: {sum(w for w, _ in words)}; largest: {words[:4]}; smallest: {words[-3:]}")

    print("\n## Problems found\n")
    for p in problems or ["none"]:
        print("-", p)


if __name__ == "__main__":
    sys.exit(main())
