// The Low Republic wiki: search.
//  - Suggestions under the search box as you type (titles and redirect names).
//  - Enter opens an exact title or redirect match; anything else opens the results page.
//  - The results page (search/?q=...) ranks every article containing the words, with snippets.
// Matching ignores capitals, accents and apostrophes ("padme" finds Padmé, "dokass" Do'Kass).
(() => {
  const root = document.documentElement.dataset.root || "";
  const MAX_SUGGESTIONS = 8;

  // ---- text helpers ------------------------------------------------------------
  const stripMarks = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "");
  const norm = (s) => stripMarks(s).toLowerCase().replace(/['’‘`]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
  // fold keeps the string's length, so positions found in it can be used on the original text
  const fold = (s) => Array.from(s, (c) => { const f = stripMarks(c).toLowerCase(); return f.length === 1 ? f : c; }).join("");
  const escapeHtml = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const href = (url, anchor, from) =>
    root + url + (from ? "?from=" + encodeURIComponent(from) : "") + (anchor ? "#" + anchor : "") || "./";

  // ---- data ------------------------------------------------------------------------
  let titlesData = null, textData = null;
  const loadTitles = () => titlesData || (titlesData = fetch(root + "search/titles.json").then((r) => r.json()).then((list) => {
    const names = [];
    for (const e of list) {
      const n = norm(e.t);
      names.push({ entry: e, label: e.t, norm: n, bare: n.replace(/^the /, ""), anchor: "", redirect: false });
      for (const [name, anchor] of e.r) {
        const rn = norm(name);
        names.push({ entry: e, label: name, norm: rn, bare: rn.replace(/^the /, ""), anchor, redirect: true });
      }
    }
    return { list, names };
  }));
  const loadText = () => textData || (textData = fetch(root + "search/text.json").then((r) => r.json()));

  // ---- suggestions ----------------------------------------------------------------
  function scoreName(name, q, words) {
    let s = 0;
    if (name.norm === q) s = 100;
    else if (name.norm.startsWith(q)) s = 90 - Math.min(name.norm.length - q.length, 40) / 10;
    else if (name.bare.startsWith(q)) s = 85 - Math.min(name.bare.length - q.length, 40) / 10;
    else {
      const parts = name.norm.split(" ");
      if (words.every((w) => parts.some((p) => p.startsWith(w)))) s = 70 - parts.length;
      else if (q.length >= 3 && name.norm.includes(q)) s = 40;
    }
    return s && name.redirect ? s - 5 : s;
  }

  function suggest(data, query) {
    const q = norm(query);
    if (!q) return [];
    const words = q.split(" ");
    // One suggestion per article, ranked by its best-matching name. The title is shown
    // whenever it matches too; a redirect name is shown only when the title does not match.
    const best = new Map();
    for (const name of data.names) {
      const s = scoreName(name, q, words);
      if (!s) continue;
      const cur = best.get(name.entry.u) || { score: 0, name: null, title: null };
      if (!name.redirect) cur.title = name;
      if (s > cur.score) { cur.score = s; cur.name = name; }
      best.set(name.entry.u, cur);
    }
    return [...best.values()]
      .map((b) => ({ name: b.title || b.name, score: b.score }))
      .sort((a, b) => b.score - a.score || a.name.entry.t.localeCompare(b.name.entry.t))
      .slice(0, MAX_SUGGESTIONS);
  }

  function exactMatch(data, query) {
    const q = norm(query);
    return data.names.find((n) => n.norm === q && !n.redirect) || data.names.find((n) => n.norm === q) || null;
  }

  function targetOf(name) {
    return name.redirect ? href(name.entry.u, name.anchor, name.label) : href(name.entry.u, "", "");
  }

  function setupBox(form) {
    const input = form.querySelector("input[name=q]");
    const list = form.querySelector(".suggestions");
    if (!input || !list) return;
    let items = [], active = -1;

    const close = () => { list.hidden = true; input.setAttribute("aria-expanded", "false"); input.removeAttribute("aria-activedescendant"); active = -1; };
    const highlight = (i) => {
      active = i;
      list.querySelectorAll("[role=option]").forEach((el, k) => el.setAttribute("aria-selected", String(k === i)));
      if (i >= 0) input.setAttribute("aria-activedescendant", "suggestion-" + i);
      else input.removeAttribute("aria-activedescendant");
    };
    const render = (results, query) => {
      items = results.map((r) => ({ href: targetOf(r.name), name: r.name }));
      items.push({ href: root + "search/?q=" + encodeURIComponent(query), all: true });
      list.innerHTML = items.map((it, i) => {
        if (it.all) {
          return `<li role="option" id="suggestion-${i}" aria-selected="false" class="suggestion-all">` +
            `<a href="${it.href}" tabindex="-1">Search all articles for <strong>${escapeHtml(query)}</strong></a></li>`;
        }
        const e = it.name.entry;
        const meta = it.name.redirect
          ? "→ " + escapeHtml(e.t) + (it.name.anchor ? " §" : "")
          : escapeHtml(e.c) + (e.x ? " · " + escapeHtml(e.x.length > 90 ? e.x.slice(0, 88).replace(/\s+\S*$/, "") + "…" : e.x) : "");
        return `<li role="option" id="suggestion-${i}" aria-selected="false">` +
          `<a href="${it.href}" tabindex="-1"><span class="suggestion-title">${escapeHtml(it.name.label)}</span>` +
          `<span class="suggestion-meta">${meta}</span></a></li>`;
      }).join("");
      list.hidden = false;
      input.setAttribute("aria-expanded", "true");
      highlight(-1);
    };

    let pending = 0;
    input.addEventListener("input", async () => {
      const query = input.value.trim();
      if (!query) return close();
      const ticket = ++pending;
      const data = await loadTitles();
      if (ticket !== pending) return; // a newer keystroke has taken over
      render(suggest(data, query), query);
    });
    input.addEventListener("focus", () => { loadTitles(); if (input.value.trim() && list.children.length) { list.hidden = false; input.setAttribute("aria-expanded", "true"); } });
    input.addEventListener("keydown", (e) => {
      if (list.hidden) return;
      if (e.key === "ArrowDown") { e.preventDefault(); highlight((active + 1) % items.length); }
      else if (e.key === "ArrowUp") { e.preventDefault(); highlight(active <= 0 ? items.length - 1 : active - 1); }
      else if (e.key === "Escape") { close(); }
      else if (e.key === "Enter" && active >= 0) { e.preventDefault(); location.href = items[active].href; }
    });
    list.addEventListener("mousedown", (e) => e.preventDefault()); // keep focus so the click lands
    input.addEventListener("blur", () => setTimeout(close, 100));
    document.addEventListener("click", (e) => { if (!form.contains(e.target)) close(); });

    // Enter without a highlighted suggestion: an exact title or redirect opens directly
    form.addEventListener("submit", async (e) => {
      const query = input.value.trim();
      e.preventDefault();
      if (!query) return;
      try {
        const match = exactMatch(await loadTitles(), query);
        location.href = match ? targetOf(match) : root + "search/?q=" + encodeURIComponent(query);
      } catch (err) {
        location.href = root + "search/?q=" + encodeURIComponent(query);
      }
    });
  }

  // ---- results page ------------------------------------------------------------------
  function countHits(haystack, term, limit) {
    let n = 0, i = haystack.indexOf(term);
    while (i !== -1 && n < limit) {
      const before = i === 0 ? " " : haystack[i - 1];
      if (term.length >= 3 || !/[a-z0-9]/.test(before)) n++; // short terms must start a word
      i = haystack.indexOf(term, i + term.length);
    }
    return n;
  }

  function firstHit(folded, terms) {
    let best = -1;
    for (const t of terms) {
      const i = folded.indexOf(t);
      if (i !== -1 && (best === -1 || i < best)) best = i;
    }
    return best;
  }

  function snippet(text, folded, terms) {
    const pos = firstHit(folded, terms);
    if (pos === -1) return "";
    let start = Math.max(0, pos - 90), end = Math.min(text.length, pos + 180);
    if (start > 0) start = text.indexOf(" ", start) + 1 || start;
    if (end < text.length) end = text.lastIndexOf(" ", end) > pos ? text.lastIndexOf(" ", end) : end;
    const part = text.slice(start, end), fpart = folded.slice(start, end);
    const marks = [];
    for (const t of terms) {
      let i = fpart.indexOf(t);
      while (i !== -1) { marks.push([i, i + t.length]); i = fpart.indexOf(t, i + t.length); }
    }
    marks.sort((a, b) => a[0] - b[0]);
    let out = "", at = 0;
    for (const [a, b] of marks) {
      if (a < at) continue;
      out += escapeHtml(part.slice(at, a)) + "<mark>" + escapeHtml(part.slice(a, b)) + "</mark>";
      at = b;
    }
    out += escapeHtml(part.slice(at));
    return (start > 0 ? "… " : "") + out + (end < text.length ? " …" : "");
  }

  async function setupResults() {
    const box = document.querySelector(".search-results");
    if (!box) return;
    const query = (new URLSearchParams(location.search).get("q") || "").trim();
    document.querySelectorAll(".search input[name=q]").forEach((i) => { i.value = query; });
    if (!query) return;
    document.title = query + " · Search · " + document.title.split(" · ").pop();
    box.innerHTML = '<p class="search-summary">Searching…</p>';

    const terms = [...new Set(norm(query).split(" ").filter(Boolean))];
    const rawTerms = [...new Set(fold(query).split(/\s+/).filter(Boolean))]; // keeps apostrophes: "do'kass"
    const [titles, texts] = await Promise.all([loadTitles(), loadText()]);
    const textByUrl = new Map(texts.map((t) => [t.u, t]));
    const q = norm(query);
    const results = [];

    for (const e of titles.list) {
      const doc = textByUrl.get(e.u) || { h: [], b: "" };
      const title = norm(e.t), titleWords = title.split(" ");
      const redirectWords = e.r.map(([n]) => norm(n)).join(" ").split(" ");
      const heads = doc.h.map(norm).join(" ");
      if (doc.folded === undefined) doc.folded = fold(doc.b);
      let score = title === q ? 100 : 0, matched = true;
      for (const t of terms) {
        let s = 0;
        if (titleWords.some((w) => w.startsWith(t))) s += 40;
        if (redirectWords.some((w) => w.startsWith(t))) s += 15;
        if (heads.includes(t)) s += 8;
        const hits = Math.max(countHits(doc.folded, t, 40), ...rawTerms.map((r) => countHits(doc.folded, r, 40)));
        if (hits) s += 5 + hits;
        if (!s) { matched = false; break; }
        score += s;
      }
      if (!matched) continue;
      const phrase = fold(query);
      if (terms.length > 1 && doc.folded.includes(phrase)) score += 25;
      if (e.w) score *= e.w; // The Entire History holds everything: rank it after the articles
      results.push({ e, doc, score });
    }
    results.sort((a, b) => b.score - a.score || a.e.t.localeCompare(b.e.t));

    if (!results.length) {
      box.innerHTML = `<p class="search-summary">No articles contain <strong>${escapeHtml(query)}</strong>.</p>` +
        `<p>Check the spelling, try fewer words, or browse the categories in the sidebar.</p>`;
      return;
    }
    const shown = results.slice(0, 60);
    box.innerHTML =
      `<p class="search-summary">${results.length} article${results.length === 1 ? "" : "s"} for <strong>${escapeHtml(query)}</strong>` +
      (results.length > shown.length ? ` (showing the first ${shown.length})` : "") + `</p>` +
      `<ol class="search-results-list">` + shown.map(({ e, doc }) => {
        const snip = snippet(doc.b, doc.folded, [...terms, ...rawTerms]) || escapeHtml(e.x);
        return `<li><a class="result-title" href="${href(e.u, "", "")}">${escapeHtml(e.t)}</a>` +
          ` <span class="result-meta">${escapeHtml(e.c)}</span>` +
          (snip ? `<p class="result-snippet">${snip}</p>` : "") + `</li>`;
      }).join("") + `</ol>`;
  }

  document.querySelectorAll("form.search").forEach(setupBox);
  setupResults().catch(() => {
    const box = document.querySelector(".search-results");
    if (box) box.innerHTML = '<p class="search-summary">Search could not load. Please try again.</p>';
  });
})();
