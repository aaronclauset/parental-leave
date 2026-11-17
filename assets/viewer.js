// Graphic 2: one institution's components on a timeline (weeks after the birth), for the birth or non-birth parent,
// with its values and links to the archived source documents. Placements come from data/2018/v2.0/timelines.json.
function Viewer(sel, timelines, provenance, rows, initial) {
  const root = document.querySelector(sel);
  d3.select(root).selectAll(".viewer-wait").remove();
  const byId = new Map(rows.map(r => [r.institution_id, r]));
  const docs = new Map(provenance.map(p => [`${p.institution_id}/${p.doc_id}`, p]));
  const state = { id: initial, parent: "birth", disc: false };
  const MAX_DRAWN = 22;
  const KIND = {
    employer_paid_leave: ["paid leave", "var(--accent)", "var(--accent-edge)"],
    employer_childbirth_benefit: ["paid leave", "var(--accent)", "var(--accent-edge)"],
    employer_topup: ["paid leave", "var(--accent)", "var(--accent-edge)"],
    modified_duties: ["relief from duties", "var(--accent-light)", "var(--accent)"],
    government_benefit: ["government benefit", "var(--gray)", "var(--gray-edge)"],
    generic_sick_or_disability_plan: ["sick-leave or disability plan", "url(#hatch)", "var(--gray-edge)"],
    unpaid_leave: ["unpaid job-protected leave", "var(--pale)", "var(--pale-edge)"],
    own_accrual: ["faculty member's own balances", "#ffffff", "var(--gray-edge)"],
  };
  // picker: a full-width search box listing every institution that matches what is typed (name, state or province)
  const picker = d3.select(root).append("div").attr("class", "picker");
  // a combobox: the list of matches is announced, and the arrow keys move through it (aria-activedescendant)
  const listId = `${root.id || "viewer"}-matches`;
  picker.append("label").attr("class", "picker-label").attr("for", `${listId}-input`).text("Institution");
  const input = picker.append("input").attr("type", "search").attr("id", `${listId}-input`).attr("autocomplete", "off")
    .attr("role", "combobox").attr("aria-autocomplete", "list").attr("aria-expanded", "false").attr("aria-controls", listId)
    .attr("placeholder", "Type to find an institution, by name or state or province");
  const results = picker.append("ul").attr("role", "listbox").attr("id", listId).attr("aria-label", "matching institutions").style("display", "none");
  const open = on => { results.style("display", on ? null : "none"); input.attr("aria-expanded", String(on)); if (!on) input.attr("aria-activedescendant", null); };
  const mark = () => {
    results.selectAll("li").classed("active", (a, i) => i === active).attr("aria-selected", (a, i) => String(i === active));
    input.attr("aria-activedescendant", matches[active] ? `${listId}-${matches[active].id}` : null);
  };
  const all = rows.map(r => ({ id: r.institution_id, name: r.institution, where: r.country === "US" ? r.state_province : `${r.state_province}, Canada` }))
    .sort((a, b) => a.name.localeCompare(b.name));
  let active = 0, matches = [];
  function search() {
    const words = input.property("value").toLowerCase().split(/[\s,]+/).filter(Boolean);  // every word, in any order
    matches = all.filter(a => words.every(w => (a.name + " " + a.where).toLowerCase().includes(w)));
    active = 0;
    open(true);
    results.selectAll("li").data(matches, a => a.id).join("li")
      .attr("role", "option").attr("id", a => `${listId}-${a.id}`).html(a => `<span>${a.name}</span><span class="meta">${a.where}</span>`)
      .on("mousedown", (e, a) => { e.preventDefault(); choose(a); });
    mark();
  }
  function choose(a) { input.property("value", ""); open(false); show(a.id); }
  input.on("focus input", search).on("blur", () => open(false))
    .on("keydown", e => {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault(); active = Math.max(0, Math.min(matches.length - 1, active + (e.key === "ArrowDown" ? 1 : -1)));
        mark();
        const li = results.selectAll("li").nodes()[active]; if (li) li.scrollIntoView({ block: "nearest" });
      } else if (e.key === "Enter" && matches[active]) { choose(matches[active]); }
      else if (e.key === "Escape") { open(false); }
    });
  const top = d3.select(root).append("div").attr("class", "controls");
  const refreshers = [
    PL.seg(top.node(), [["birth", "birth parent"], ["nonbirth", "non-birth parent"]], () => state.parent, v => { state.parent = v; draw(); }, "parent"),
    PL.seg(top.node(), [[false, "guaranteed"], [true, "with discretionary"]], () => state.disc, v => { state.disc = v; draw(); }, "benefits counted"),
  ];
  const head = d3.select(root).append("div").attr("class", "viewer-head");
  const legend = d3.select(root).append("div").attr("class", "legend");
  [...new Map(Object.values(KIND).map(k => [k[0], k])).values()].forEach(([label, fill, edge]) =>
    legend.append("span").html(`<i style="background:${fill.startsWith("url") ? "repeating-linear-gradient(45deg,#fff 0 2px,#9a9a9a 2px 3px)" : fill};border:1px solid ${edge}"></i>${label}`));
  legend.append("span").html(`<i style="background:#fff;border:1px dashed var(--accent)"></i>discretionary (counted only with discretionary benefits)`);
  const chart = d3.select(root).append("div").attr("class", "chart");
  const tip = PL.tipper(chart.node());
  // the timeline's text alternative (the list below gives each component in full)
  const summaryId = `${root.id || "viewer"}-summary`;
  const summary = d3.select(root).append("p").attr("class", "visually-hidden").attr("id", summaryId);
  const list = d3.select(root).append("div").attr("class", "comp-list");

  const wk = v => (v == null ? "no stated length" : `${PL.fmt(v)} weeks`);
  // a component with no length in weeks: its stated quantity ("2 courses"), or that none is stated
  const len = c => (c.weeks != null ? wk(c.weeks) : c.counted ? `no stated end; counted to week ${PL.fmt(c.counted[1])} in job-protected weeks`
    : c.amount ? `${c.amount} (not in weeks)` : "no stated length");
  // where a component is shown from: the span the derivation counts, for a leave with no stated end; else its placement
  const from = c => (c.weeks == null && c.counted ? c.counted[0] : c.start);
  const counted = c => !c.general_purpose && !c.over_two_years;
  function sources(c) {
    return c.doc_ids.map(d => docs.get(`${state.id}/${d}`) || docs.get(`/${d}`)).filter(Boolean)
      .map(p => `<a href="${p.wayback_url || p.url}" target="_blank" rel="noopener">${p.title || p.doc_id}<span class="visually-hidden"> (opens in a new tab)</span></a>`).join("; ") || "no linked source";
  }
  function describe(c) {
    const bits = [KIND[c.mechanism] ? KIND[c.mechanism][0] : c.mechanism.replace(/_/g, " "), c.entitlement.replace(/_/g, " ")];
    if (c.pay_pct != null) bits.push(`${c.pay_pct}% pay`);
    if (!counted(c)) bits.push(c.general_purpose ? "general-purpose leave, not counted" : "requires more than two years of service, not counted");
    return bits.join(" · ");
  }
  function show(id, parent) {
    state.id = id;
    if (parent) state.parent = parent;
    draw();
    PL.announce(`Showing ${timelines[id].institution}, ${PL.parentName(state.parent)}.`);
  }
  function draw() {
    refreshers.forEach(f => f());
    const t = timelines[state.id], r = byId.get(state.id), p = t[state.parent], v = state.disc ? p.with_discretionary : p.guaranteed;
    head.html("");
    head.append("span").attr("class", "name").text(t.institution);
    head.append("span").attr("class", "vals").html(t.values_available
      ? `primary value <b>${PL.fmt(v.weeks_2018def)}</b> weeks${v.relief_2018def ? ` (${v.relief_2018def.toLowerCase()})` : ""} · paid weeks in total ${PL.fmt(v.paid_weeks_total)} · job-protected weeks up to ${PL.fmt(v.protected_weeks_max)}`
      : "values not available: the governing faculty policy was not publicly accessible");
    const comps = p.components;
    const placed = comps.filter(c => c.start != null), unplaced = comps.filter(c => c.start == null);
    chart.selectAll("p").remove();
    if (!placed.length || placed.length > MAX_DRAWN) {
      chart.selectAll("svg").remove();
      chart.append("p").attr("class", "note").text(placed.length
        ? `This policy has ${placed.length} components for this parent, too many to draw clearly; they are listed below.`
        : "No leave, pay or relief for this parent is placed in time.");
    } else drawTimeline(placed);
    list.html("");
    const group = (title, cs) => {
      if (!cs.length) return;
      list.append("h3").text(title);
      cs.forEach(c => list.append("details").html(`<summary><b>${c.id}</b> ${c.label || (KIND[c.mechanism] || [c.mechanism.replace(/_/g, " ")])[0]} — ${len(c)}${c.start != null ? `, from week ${PL.fmt(from(c))}` : ""}</summary>` +
        `<ul><li>${describe(c)}</li><li>sources: ${sources(c)}</li>` +
        `${c.links.length ? `<li>links: ${c.links.map(l => `${l.relation.replace(/_/g, " ")} ${l.to}`).join("; ")}</li>` : ""}</ul>`));
    };
    summary.text(`${t.institution}, ${PL.parentName(state.parent)}: ${placed.length} component${placed.length === 1 ? "" : "s"} placed on a timeline ` +
      `of weeks after the birth, and ${unplaced.length} other provision${unplaced.length === 1 ? "" : "s"}; each is listed below with its length and start.`);
    group(placed.length > MAX_DRAWN ? "Components" : "Components on the timeline", placed);
    group("Other provisions (not periods of leave or pay)", unplaced);
  }
  // the timeline is kept between redraws: bars move, grow and fade to their new places (about half a second)
  const T = 550;
  function drawTimeline(placed, instant = false) {
    // drawn at the chart's real width, so the labels keep their size on a phone
    const W = PL.chartWidth(chart.node(), 900), small = PL.narrow(W), rowH = 21, m = { l: small ? 132 : 230, r: 20, t: 8, b: 36 };
    const maxChars = small ? 19 : 34;
    const short = s => (s.length > maxChars ? s.slice(0, maxChars - 1).trimEnd() + "…" : s);
    // no length in weeks: drawn to week 52 only where the rules count it there (U5, job-protected weeks); otherwise a
    // short stub that marks where it starts, with its stated quantity beside it, never an invented length
    const STUB = 3;
    // a component with no length in weeks is drawn over the span the derivation counts for it in job-protected weeks
    // (`counted`, U3/U5), or else as a short stub where it starts, labelled with its stated quantity: never an
    // invented length. The stub's width marks a point; it is not a duration.
    const s0 = from;
    const end = c => (c.weeks != null ? c.start + c.weeks : c.counted ? c.counted[1] : c.start + STUB);
    // the axis covers the counted components, at least a year and at most two; longer bars are cut at the edge
    const xmax = Math.max(52, Math.min(104, d3.max(placed.filter(counted), end) || 52));
    const H = m.t + placed.length * rowH + m.b;
    const x = d3.scaleLinear().domain([0, xmax]).range([m.l, W - m.r]);
    let svg = chart.select("svg");
    const fresh = svg.empty();
    if (fresh) {
      svg = chart.append("svg").attr("role", "img").attr("aria-label", "Components on a timeline").attr("aria-describedby", summaryId)
        .attr("viewBox", `0 0 ${W} ${H}`);
      svg.append("defs").append("pattern").attr("id", "hatch").attr("patternUnits", "userSpaceOnUse").attr("width", 5).attr("height", 5)
        .attr("patternTransform", "rotate(45)").call(pt => { pt.append("rect").attr("width", 5).attr("height", 5).attr("fill", "#fff");
          pt.append("line").attr("y2", 5).attr("stroke", "#9a9a9a").attr("stroke-width", 1.4); });
      svg.append("g").attr("class", "axis");
      svg.append("text").attr("class", "xlab").attr("text-anchor", "middle").attr("font-size", 12).attr("fill", "var(--ink)").text("weeks after the birth");
      svg.append("g").attr("class", "rows");
    }
    const t = svg.transition().duration(fresh || instant ? 0 : PL.dur(T)).ease(d3.easeCubicInOut);
    const vb = svg.attr("viewBox").split(" ").map(Number), h0 = vb[2] === W ? vb[3] : H;
    if (vb[2] !== W) svg.attr("viewBox", `0 0 ${W} ${H}`);
    t.attrTween("viewBox", () => tt => `0 0 ${W} ${h0 + (H - h0) * tt}`);
    const ticks = d3.range(0, xmax + 1, xmax > 80 || small ? 16 : 8);
    svg.select("g.axis").transition(t).attr("transform", `translate(0,${H - m.b + 4})`)
      .call(d3.axisBottom(x).tickValues(ticks).tickSize(-(H - m.t - m.b + 4)))
      .on("end", function () { d3.select(this).selectAll(".tick line").attr("stroke", "var(--rule)"); });
    svg.select("g.axis").call(a => a.selectAll(".tick line").attr("stroke", "var(--rule)")).call(a => a.select(".domain").remove())
      .call(a => a.selectAll("text").attr("font-size", 12).attr("fill", "var(--ink)"));
    svg.select("text.xlab").attr("x", (m.l + W - m.r) / 2).transition(t).attr("y", H - 4);
    const look = c => {
      const k = KIND[c.mechanism] || ["other", "#fff", "var(--gray-edge)"];
      const disc = !["guaranteed", "guaranteed_on_request"].includes(c.entitlement);
      return { k, disc, faded: !counted(c) || (disc && !state.disc), cut: end(c) > xmax,
        x0: x(Math.min(s0(c), xmax)), w: Math.max(2, x(Math.min(end(c), xmax)) - x(Math.min(s0(c), xmax))) };
    };
    const rows = svg.select("g.rows").selectAll("g.row").data(placed, c => `${state.id}/${c.id}`);
    rows.exit().transition(t).style("opacity", 0).remove();
    const enter = rows.enter().append("g").attr("class", "row").style("opacity", 0)
      .attr("transform", (c, i) => `translate(0,${m.t + i * rowH})`);
    enter.append("text").attr("class", "lab").call(s => s.append("title")).attr("x", m.l - 8).attr("y", rowH / 2 + 4).attr("text-anchor", "end").attr("font-size", 11.5);
    enter.append("rect").attr("class", "bar").attr("y", 3).attr("height", rowH - 6).attr("rx", 2)
      .attr("x", c => look(c).x0).attr("width", 0);
    enter.append("text").attr("class", "cut").attr("x", W - m.r + 2).attr("y", rowH / 2 + 4).attr("font-size", 11).attr("fill", "var(--ink-2)");
    enter.append("text").attr("class", "open").attr("y", rowH / 2 + 4).attr("font-size", 10.5).attr("fill", "var(--ink-2)");
    const all = enter.merge(rows);
    all.transition(t).delay(fresh || instant ? 0 : PL.dur(T / 4)).style("opacity", 1).attr("transform", (c, i) => `translate(0,${m.t + i * rowH})`);
    all.select("text.lab").attr("x", m.l - 8).each(function (c) {
      const full = `${c.id} ${c.label || look(c).k[0]}`;
      d3.select(this).text(short(full)).append("title").text(full);  // the full name on hover; the list below has it too
    }).attr("fill", c => (look(c).faded ? "var(--muted)" : "var(--ink)"));
    all.select("text.cut").attr("x", W - m.r + 2);
    all.select("text.cut").text(c => (look(c).cut ? "→" : ""));
    all.select("text.open").attr("x", c => (c.counted ? x(Math.min(s0(c), xmax)) + 4 : x(Math.min(end(c), xmax)) + 4))
      .text(c => (c.weeks != null ? "" : c.counted ? `no stated end: counted to week ${PL.fmt(c.counted[1])} (job-protected weeks)`
        : c.amount ? `${c.amount}, not in weeks` : "length not stated"));
    all.select("rect.bar")
      .attr("fill", c => look(c).k[1]).attr("stroke", c => (look(c).disc ? "var(--accent)" : look(c).k[2]))
      .attr("stroke-width", c => (look(c).disc ? 1.2 : 0.8)).attr("stroke-dasharray", c => (look(c).disc ? "4 2" : null))
      .on("mouseenter mousemove", (e, c) => tip.show(e, `<b>${c.id} ${c.label || ""}</b><br>${describe(c)}<br>${len(c)}, from week ${PL.fmt(from(c))}`))
      .on("mouseleave", () => tip.hide())
      .transition(t).delay(fresh || instant ? 0 : PL.dur(T / 4)).duration(fresh || instant ? 0 : PL.dur(T))
      .attr("x", c => look(c).x0).attr("width", c => look(c).w).attr("opacity", c => (look(c).faded ? 0.6 : 1));
  }
  draw();
  PL.onResize(chart.node(), () => {
    const placed = timelines[state.id][state.parent].components.filter(c => c.start != null);
    if (placed.length && placed.length <= MAX_DRAWN) drawTimeline(placed, true);
  });
  return { show(id, parent) { show(id, parent); root.scrollIntoView({ behavior: PL.scrollBehavior(), block: "start" }); } };
}
