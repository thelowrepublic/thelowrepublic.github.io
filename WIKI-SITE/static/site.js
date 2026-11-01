// The Low Republic wiki: menu drawer, "Redirected from" note, contents highlighting,
// image lightbox and the entry disclaimer.
(() => {
  const html = document.documentElement;
  const body = document.body;
  const sidebar = document.getElementById("sidebar");
  const pageParts = () => [document.querySelector(".topbar"), document.querySelector(".layout")];

  // ---- Menu drawer (narrow screens) -----------------------------------------
  function setupMenu() {
    const button = document.querySelector(".menu-button");
    const scrim = document.querySelector(".nav-scrim");
    const setNav = (open) => {
      body.classList.toggle("nav-open", open);
      if (button) button.setAttribute("aria-expanded", String(open));
      if (scrim) scrim.hidden = !open;
    };
    if (button) button.addEventListener("click", () => setNav(!body.classList.contains("nav-open")));
    if (scrim) scrim.addEventListener("click", () => setNav(false));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setNav(false); });
    if (sidebar) sidebar.addEventListener("click", (e) => { if (e.target.closest("a")) setNav(false); });
  }

  // ---- "Redirected from X" ---------------------------------------------------
  function setupRedirectNote() {
    const from = new URLSearchParams(location.search).get("from");
    const note = document.querySelector(".redirect-note");
    if (!from || !note) return;
    note.textContent = "Redirected from " + from;
    note.hidden = false;
    history.replaceState(null, "", location.pathname + location.hash); // show the article's own address
  }

  // ---- Highlight the section being read in the sidebar contents ---------------
  function setupContents() {
    const links = Array.from(document.querySelectorAll(".toc-sidebar .toc-list a"));
    if (!links.length) return;
    const byId = new Map(links.map((a) => [decodeURIComponent(a.hash.slice(1)), a]));
    const heads = Array.from(document.querySelectorAll(".article-body h2[id], .article-body h3[id]"))
      .filter((h) => byId.has(h.id));
    const topLink = byId.get("top");
    let current = null;

    const update = () => {
      const line = parseInt(getComputedStyle(html).getPropertyValue("--topbar-h"), 10) + 40;
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
      const box = sidebar.getBoundingClientRect(); // keep the entry visible in a long list
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
  }

  // ---- Lightbox: click an image to see it larger ------------------------------
  // The image fills the window's height (or width, if that is tighter), the page behind
  // darkens, "Open full image" opens the original in a new tab, and a click on the dark
  // background (or Esc) closes it. Without JavaScript the image link opens the original.
  function setupLightbox() {
    const box = document.createElement("div");
    box.className = "lightbox";
    box.hidden = true;
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.setAttribute("aria-label", "Artwork");
    box.innerHTML =
      '<div class="lightbox-frame">' +
      '<div class="lightbox-picture"><img class="lightbox-img" alt="">' +
      '<a class="lightbox-open" target="_blank" rel="noopener">Open full image <span aria-hidden="true">↗</span></a></div>' +
      '<div class="lightbox-caption"></div></div>';
    body.append(box);
    const img = box.querySelector(".lightbox-img");
    const open = box.querySelector(".lightbox-open");
    const caption = box.querySelector(".lightbox-caption");
    let size = null;
    let returnTo = null;

    const fit = () => {
      if (!size) return;
      const room = caption.textContent.trim() ? 72 : 32; // space below for the credit
      const scale = Math.min((window.innerHeight - 32 - room) / size.h, (window.innerWidth - 32) / size.w);
      img.style.width = Math.max(1, Math.round(size.w * scale)) + "px";
      img.style.height = Math.max(1, Math.round(size.h * scale)) + "px";
    };
    const show = (link) => {
      const w = Number(link.dataset.w), h = Number(link.dataset.h);
      size = w && h ? { w, h } : null;
      img.removeAttribute("style");
      img.src = link.dataset.large || link.href;
      const thumb = link.querySelector("img");
      img.alt = thumb ? thumb.alt : "";
      open.href = link.href;
      const figcaption = link.closest("figure") && link.closest("figure").querySelector("figcaption");
      caption.innerHTML = figcaption ? figcaption.innerHTML : "";
      returnTo = link;
      box.hidden = false;
      html.classList.add("lightbox-active");
      fit();
      open.focus({ preventScroll: true });
    };
    const hide = () => {
      if (box.hidden) return;
      box.hidden = true;
      html.classList.remove("lightbox-active");
      img.removeAttribute("src");
      if (returnTo) returnTo.focus({ preventScroll: true });
    };

    img.addEventListener("load", () => {
      if (!size && img.naturalWidth) { size = { w: img.naturalWidth, h: img.naturalHeight }; fit(); }
    });
    document.addEventListener("click", (e) => {
      const link = e.target.closest("a.image-link");
      if (!link || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      show(link);
    });
    box.addEventListener("click", (e) => {
      if (!e.target.closest(".lightbox-picture, .lightbox-caption a")) hide();
    });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });
    document.addEventListener("focusin", (e) => { if (!box.hidden && !box.contains(e.target)) open.focus(); });
    window.addEventListener("resize", fit);
  }

  // ---- Entry disclaimer ----------------------------------------------------------
  // The head script adds .gate-open before the page is drawn; this wires up the button
  // and the footer's "Disclaimer" link, which shows the notice again.
  function setupDisclaimer() {
    const gate = document.getElementById("disclaimer");
    if (!gate) return;
    const button = gate.querySelector(".gate-button");
    const setOpen = (open) => {
      html.classList.toggle("gate-open", open);
      pageParts().forEach((el) => { if (el) el.inert = open; });
      if (open) button.focus({ preventScroll: true });
    };
    button.addEventListener("click", () => {
      try { localStorage.setItem("lowrepublic-disclaimer", gate.dataset.version); } catch (e) { /* private mode */ }
      setOpen(false);
    });
    document.querySelectorAll("[data-open-disclaimer]").forEach((el) =>
      el.addEventListener("click", () => setOpen(true)));
    if (html.classList.contains("gate-open")) setOpen(true);
  }

  // ---- Category pages: filter by period and region -------------------------------
  function setupFilters() {
    const form = document.querySelector(".filters");
    if (!form) return;
    form.hidden = false;
    const items = Array.from(document.querySelectorAll(".category-list li"));
    const groups = Array.from(document.querySelectorAll(".letter-group"));
    const letters = Array.from(document.querySelectorAll(".letter-bar a"));
    const count = form.querySelector(".filter-count");
    const empty = document.querySelector(".filter-empty");
    const value = (name) => (form.elements[name] ? form.elements[name].value : "");
    const apply = () => {
      const period = value("period"), region = value("region");
      let shown = 0;
      for (const li of items) {
        const ok = (!period || li.dataset.periods.split("|").includes(period)) &&
                   (!region || li.dataset.regions.split("|").includes(region));
        li.hidden = !ok;
        if (ok) shown++;
      }
      for (const g of groups) g.hidden = !g.querySelector("li:not([hidden])");
      for (const a of letters) {
        const g = groups.find((x) => x.dataset.letter === a.dataset.letter);
        a.classList.toggle("empty", !g || g.hidden);
      }
      count.textContent = period || region ? "Showing " + shown + " of " + items.length : "";
      if (empty) empty.hidden = shown > 0;
    };
    form.addEventListener("change", apply);
    form.addEventListener("submit", (e) => e.preventDefault());
    apply();
  }

  setupDisclaimer();
  setupFilters();
  // Record page transition: text below the first screen is shown straight away, so long
  // pages do not animate hundreds of lines nobody can see yet.
  function setupTransition() {
    var html = document.documentElement;
    if (!html.classList.contains("animate-in") || html.getAttribute("data-transition") !== "record") return;
    var fold = window.innerHeight;
    document.querySelectorAll(".content :is(h2, h3, h4, p, li, th, td, dt, dd, figcaption, summary, .hatnote)")
      .forEach(function (el) { if (el.getBoundingClientRect().top > fold) el.classList.add("tr-skip"); });
  }

  // The Animations switch beside the search box: remembered in this browser, and off (and fixed)
  // when the device asks for reduced motion.
  function setupAnimationSwitch() {
    var button = document.querySelector(".anim-switch");
    if (!button) return;
    var html = document.documentElement;
    var reduce = html.classList.contains("motion-reduced");
    function show() {
      var on = !reduce && !html.classList.contains("animations-off");
      button.setAttribute("aria-checked", on ? "true" : "false");
      button.title = reduce ? "Animations are off because your device is set to reduce motion"
                            : on ? "Page animations are on. Click to turn them off." : "Page animations are off. Click to turn them on.";
    }
    if (reduce) button.disabled = true;
    button.addEventListener("click", function () {
      var off = html.classList.toggle("animations-off");
      try { localStorage.setItem("lowrepublic-animations", off ? "off" : "on"); } catch (e) {}
      show();
    });
    show();
  }

  setupTransition();
  setupAnimationSwitch();
  setupMenu();
  setupRedirectNote();
  setupContents();
  setupLightbox();
})();
