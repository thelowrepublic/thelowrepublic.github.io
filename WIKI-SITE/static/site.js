// The Low Republic wiki: menu drawer, contents highlighting, "Redirected from" note.
(() => {
  const body = document.body;
  const button = document.querySelector(".menu-button");
  const scrim = document.querySelector(".nav-scrim");
  const sidebar = document.getElementById("sidebar");

  // ---- Menu drawer (narrow screens) -----------------------------------------
  const setNav = (open) => {
    body.classList.toggle("nav-open", open);
    if (button) button.setAttribute("aria-expanded", String(open));
    if (scrim) scrim.hidden = !open;
  };
  if (button) button.addEventListener("click", () => setNav(!body.classList.contains("nav-open")));
  if (scrim) scrim.addEventListener("click", () => setNav(false));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") setNav(false); });
  if (sidebar) sidebar.addEventListener("click", (e) => { if (e.target.closest("a")) setNav(false); });

  // ---- "Redirected from X" ---------------------------------------------------
  const params = new URLSearchParams(location.search);
  const from = params.get("from");
  const note = document.querySelector(".redirect-note");
  if (from && note) {
    note.textContent = "Redirected from " + from;
    note.hidden = false;
    // Show the article's own address, as a wiki does after a redirect.
    history.replaceState(null, "", location.pathname + location.hash);
  }

  // ---- Highlight the section being read in the sidebar contents ---------------
  const links = Array.from(document.querySelectorAll(".toc-sidebar .toc-list a"));
  if (!links.length) return;
  const byId = new Map(links.map((a) => [decodeURIComponent(a.hash.slice(1)), a]));
  const heads = Array.from(document.querySelectorAll(".article-body h2[id], .article-body h3[id]"))
    .filter((h) => byId.has(h.id));
  const topLink = byId.get("top");
  let current = null;

  const update = () => {
    const line = parseInt(getComputedStyle(document.documentElement).getPropertyValue("--topbar-h"), 10) + 40;
    let active = topLink;
    for (const h of heads) {
      if (h.getBoundingClientRect().top - line <= 0) active = byId.get(h.id);
      else break;
    }
    if (active === current) return;
    if (current) current.classList.remove("active");
    current = active;
    if (!current) return;
    current.classList.add("active");
    // keep the active entry visible in a long, scrolling contents list
    const box = sidebar.getBoundingClientRect();
    const r = current.getBoundingClientRect();
    if (r.top < box.top + 40 || r.bottom > box.bottom - 40) {
      sidebar.scrollTop += r.top - box.top - box.height / 2;
    }
  };

  let queued = false;
  window.addEventListener("scroll", () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; update(); });
  }, { passive: true });
  update();
})();
