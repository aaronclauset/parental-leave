// Shared data loading and helpers. Every number shown on the site is computed here from the released files.
const PL = (() => {
  // the site's root, from this script's own address (assets/common.js), so pages in subfolders load the same files
  const BASE = new URL("..", document.currentScript.src).href;
  const VERSION = "data/2018/v2.0/";  // the current release's folder
  const FILES = {
    csv: VERSION + "parental_leave_2018_v2.0.csv",
    diffs: VERSION + "v1_v2_differences.csv",
    timelines: VERSION + "timelines.json",
    provenance: VERSION + "provenance/index.csv",
    manifest: VERSION + "files.json",
    tiers: VERSION + "reference/component_tiers.csv",
  };
  const NUM = /(_weeks|_weeks_max|_equiv_weeks|_total|_plan_weeks|_protected_weeks_max|_floor_.*_weeks)(_disc)?$|^term_weeks$|^n_|^prestige_rank$|^aau_member_2018$/;
  const num = v => (v === "" || v == null ? null : +v);
  const fmt = v => (v == null ? "–" : (Math.round(v * 10) / 10).toLocaleString("en-US", { maximumFractionDigits: 1 }));
  const median = a => { const b = a.filter(x => x != null).sort((x, y) => x - y); const n = b.length;
    return n ? (n % 2 ? b[(n - 1) / 2] : (b[n / 2 - 1] + b[n / 2]) / 2) : null; };
  const pct = (k, n) => (n ? Math.round((100 * k) / n) : 0);

  // motion: none when the reader's system asks for reduced motion
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const dur = ms => (reducedMotion.matches ? 0 : ms);
  const scrollBehavior = () => (reducedMotion.matches ? "auto" : "smooth");

  // numbers computed from the data show a dash until the data arrive
  function placeholders() {
    document.querySelectorAll("[data-n]").forEach(e => { if (!e.textContent.trim()) e.textContent = "–"; });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", placeholders);
  else placeholders();

  // a failed request leaves a short message at the top of the page instead of silent gaps
  function loadFailed(err) {
    console.error(err);
    if (document.getElementById("load-error")) return;
    const main = document.querySelector("main");
    if (!main) return;
    const p = document.createElement("p");
    p.id = "load-error";
    p.className = "load-error";
    p.setAttribute("role", "alert");
    p.innerHTML = "The data files could not be loaded, so the figures and computed numbers on this page are missing. " +
      "Reload the page, or get the files from the <a href=\"https://github.com/aaronclauset/parental-leave\">GitHub repository</a>.";
    main.prepend(p);
  }

  let cache = {};
  async function load(...which) {
    const out = {};
    try {
      await Promise.all(which.map(async k => {
        if (!cache[k]) {
          if (k === "timelines" || k === "manifest") cache[k] = d3.json(BASE + FILES[k]);
          else cache[k] = d3.csv(BASE + FILES[k], r => {
            if (k === "csv") for (const c in r) if (NUM.test(c)) r[c] = num(r[c]);
            return r;
          });
        }
        out[k] = await cache[k];
      }));
    } catch (err) {
      which.forEach(k => delete cache[k]);  // allow a later retry
      loadFailed(err);
      throw err;
    }
    return out;
  }

  // charts are drawn at their real width (so text keeps its size on a phone) and redrawn when the width changes
  const narrow = w => w < 560;
  const chartWidth = (el, max) => Math.max(300, Math.min(max, Math.floor(el.getBoundingClientRect().width || max)));
  function onResize(el, redraw) {
    let last = el.getBoundingClientRect().width, timer = null;
    new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width;
      if (Math.abs(w - last) < 8) return;
      last = w;
      clearTimeout(timer);
      timer = setTimeout(redraw, 120);
    }).observe(el);
  }

  // one polite status region per page: announces changes a screen-reader user would otherwise miss (debounced)
  let statusEl = null, statusTimer = null;
  function announce(msg, delay = 400) {
    if (!statusEl) {
      statusEl = document.createElement("div");
      statusEl.className = "visually-hidden";
      statusEl.setAttribute("role", "status");
      document.body.append(statusEl);
    }
    clearTimeout(statusTimer);
    statusTimer = setTimeout(() => { statusEl.textContent = msg; }, delay);
  }
  // a chart's text alternative: a visually hidden summary of what it shows, linked (with the chart's visible caption,
  // if any) through aria-describedby; update() rewrites it whenever the view changes
  function describe(svgSel, id, captionId) {
    const svg = svgSel.node(), p = document.createElement("p");
    p.id = id;
    p.className = "visually-hidden";
    svg.parentNode.after(p);
    svg.setAttribute("aria-describedby", captionId ? `${id} ${captionId}` : id);
    return text => { p.textContent = text; };
  }

  // values available, with the column name for a parent and variant
  const col = (parent, disc, what = "weeks") => `${parent}_${what}${disc ? "_disc" : ""}`;
  const parentName = p => (p === "birth" ? "birth parent" : "non-birth parent");
  const regionOrder = ["Northeast", "Midwest", "South", "West", "Canada"];
  function sideNav() {
    const links = [...document.querySelectorAll("#toc a[href^='#']")];
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (!e.isIntersecting) return;
      links.forEach(a => {
        const on = a.getAttribute("href") === "#" + e.target.id;
        a.classList.toggle("on", on);
        if (on) a.setAttribute("aria-current", "location"); else a.removeAttribute("aria-current");
      });
    }), { rootMargin: "-35% 0px -60% 0px" });
    document.querySelectorAll("main section[id]").forEach(s => io.observe(s));
    const btn = document.querySelector(".menu-btn"), toc = document.getElementById("toc");
    if (btn && toc) {
      btn.setAttribute("aria-controls", "toc");
      btn.setAttribute("aria-expanded", "false");
      btn.addEventListener("click", () => btn.setAttribute("aria-expanded", String(toc.classList.toggle("open"))));
      // on a phone, choosing a section closes the menu again
      toc.addEventListener("click", e => {
        if (e.target.closest("a") && toc.classList.contains("open")) { toc.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); }
      });
    }
  }
  function tipper(root) {
    const tip = d3.select(root).append("div").attr("class", "tip").attr("aria-hidden", "true");
    return {
      show(e, html) {
        const b = root.getBoundingClientRect();
        let x = e.clientX - b.left + 14, y = e.clientY - b.top - 10;
        if (x > b.width - 260) x = Math.max(0, e.clientX - b.left - 270);
        tip.html(html).style("left", x + "px").style("top", y + "px").style("opacity", 1);
      },
      hide() { tip.style("opacity", 0); },
    };
  }
  // a set of toggle buttons; the pressed one is announced to screen readers (aria-pressed)
  function seg(parent, items, get, set, label) {
    const g = d3.select(parent).append("div").attr("class", "seg").attr("role", "group");
    if (label) g.attr("aria-label", label);
    items.forEach(([v, text]) => g.append("button").attr("type", "button").text(text).datum(v)
      .on("click", () => { set(v); refresh(); }));
    const refresh = () => g.selectAll("button").classed("on", v => v === get()).attr("aria-pressed", v => String(v === get()));
    refresh();
    return refresh;
  }
  return { BASE, VERSION, FILES, load, num, fmt, median, pct, col, parentName, regionOrder, sideNav, tipper, seg,
    dur, scrollBehavior, narrow, chartWidth, onResize, announce, describe };
})();
