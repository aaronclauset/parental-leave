// Graphic 1: every institution's primary value as a beeswarm, by group, with controls, search and hover details.
// Clicking an institution opens it in the policy viewer (graphic 2), if the page has one.
function Explorer(sel, rows, opts = {}) {
  const root = document.querySelector(sel);
  const state = { parent: "birth", disc: false, group: "none", find: "" };
  // limits on use: stated limits on how often a primary component may be used (the use_limits column, with each
  // component's tier from reference/component_tiers.csv); "per career" is a lifetime limit, "per N years" a per-period one
  const limits = new Map();  // institution_id -> { kind, text }
  let limitsReady = null;
  function loadLimits() {
    if (!limitsReady) limitsReady = PL.load("tiers").then(({ tiers }) => {
      const tier = new Map(tiers.map(t => [t.component_id, t.tier]));
      rows.forEach(d => {
        let career = false, period = false;
        const parts = [];
        for (const m of (d.use_limits || "").matchAll(/(\S+_c\d+) \(([^)]*)\): ([^;]+)/g)) {
          if (tier.get(m[1]) !== "primary") continue;
          m[3].split(", ").forEach(p => {
            if (/per career/.test(p)) career = true; else if (/per \d+ years?/.test(p)) period = true; else return;
            parts.push(p);
          });
        }
        const kind = career && period ? "both limits" : career ? "lifetime limit" : period ? "per-period limit" : "no stated limit";
        limits.set(d.institution_id, { kind, text: [...new Set(parts)].join(", ") });
      });
    });
    return limitsReady;
  }
  const groups = {
    none: { label: "all institutions", key: () => "All institutions", order: ["All institutions"] },
    country: { label: "country", key: d => (d.country === "US" ? "United States" : "Canada"), order: ["United States", "Canada"] },
    region: { label: "region", key: d => d.region, order: PL.regionOrder },
    control: { label: "public or private (U.S.)", key: d => (d.country !== "US" ? null : d.control === "private" ? "U.S. private" : "U.S. public"),
      order: ["U.S. public", "U.S. private"] },
    aau: { label: "AAU membership", key: d => (d.aau_member_2018 ? "AAU member" : "not a member"), order: ["AAU member", "not a member"] },
    limits: { label: "limits on use", key: d => (limits.get(d.institution_id) || {}).kind,
      order: ["lifetime limit", "per-period limit", "both limits", "no stated limit"], needs: loadLimits },
  };
  const data = rows.filter(d => d.values_available === "yes");
  const controls = d3.select(root).append("div").attr("class", "controls");
  const refreshers = [
    PL.seg(controls.node(), [["birth", "birth parent"], ["nonbirth", "non-birth parent"]], () => state.parent, v => { state.parent = v; draw(); }, "parent"),
    PL.seg(controls.node(), [[false, "guaranteed"], [true, "with discretionary"]], () => state.disc, v => { state.disc = v; draw(); }, "benefits counted"),
  ];
  const pick = controls.append("label").text("group by ");
  const select = pick.append("select").on("change", async e => {
    const g = groups[e.target.value];
    if (g.needs) { try { await g.needs(); } catch (err) { select.property("value", state.group); return; } }
    state.group = e.target.value;
    draw();
    PL.announce(summaryText);
  });
  Object.entries(groups).forEach(([k, g]) => select.append("option").attr("value", k).text(g.label));
  controls.append("label").text("find ").append("input").attr("type", "search").attr("placeholder", "an institution")
    .on("input", e => { state.find = e.target.value.trim().toLowerCase(); highlight(); });
  const chart = d3.select(root).append("div").attr("class", "chart");
  const svg = chart.append("svg").attr("role", "img").attr("aria-label", "Weeks of paid leave or relief at each institution");
  const tip = PL.tipper(chart.node());
  const summary = PL.describe(svg, `${root.id}-summary`, opts.captionId);
  let summaryText = "";
  let W = 900, R = 3.7, rowH = 74;
  const m = { l: 150, r: 16, t: 8, b: 40 };
  const x = d3.scaleLinear().domain([-1, 54]);

  function swarm(points, cy, half) {
    // stack dots vertically at their value first, and spread sideways only a little, allowing a small overlap,
    // so that each dot stays close to its true value
    const placed = [], step = R * 1.15, ny = Math.floor((half - R) / step), cands = [];
    for (let j = 0; j < 30; j++) for (let i = -ny; i <= ny; i++) cands.push([(j % 2 ? 1 : -1) * Math.ceil(j / 2) * R * 0.9, i * step]);
    cands.sort((u, v) => Math.hypot(u[0] * 4, u[1]) - Math.hypot(v[0] * 4, v[1]));
    points.sort((a, b) => a.v - b.v).forEach(p => {
      const x0 = x(Math.min(p.v, 53));
      const ok = (px, py) => px >= m.l + R && placed.every(q => Math.hypot(q.px - px, q.py - py) >= 1.55 * R);
      const c = cands.find(([dx, dy]) => ok(x0 + dx, cy + dy)) || [0, 0];
      placed.push({ ...p, px: x0 + c[0], py: cy + c[1] });
    });
    return placed;
  }
  function highlight() {
    gDots.selectAll("circle.dot").attr("r", d => (state.find && d.d.institution.toLowerCase().includes(state.find) ? R + 2.5 : R))
      .attr("fill", d => (state.find && d.d.institution.toLowerCase().includes(state.find) ? "var(--ink)" : "var(--accent)"));
  }
  const gAxis = svg.append("g"), gRows = svg.append("g"), gDots = svg.append("g"), xLabel = svg.append("text");
  let H0 = null, W0 = null;
  const T = 650;  // milliseconds: dots glide to their new places when the view changes
  function draw(instant = false) {
    refreshers.forEach(f => f());
    select.property("value", state.group);
    W = PL.chartWidth(chart.node(), 900);
    const small = PL.narrow(W);
    m.l = small ? 112 : 150;
    R = small ? 3 : 3.7;
    x.range([m.l, W - m.r]);
    const g = groups[state.group], c = PL.col(state.parent, state.disc), rc = PL.col(state.parent, state.disc, "relief");
    const rowsG = g.order.map(name => ({ name, pts: data.filter(d => g.key(d) === name).map(d => ({ d, v: d[c] })) }));
    rowH = rowsG.length === 1 ? 190 : rowsG.length === 2 ? 120 : 84;
    const H = m.t + rowsG.length * rowH + m.b;
    const t = svg.transition().duration(H0 == null || instant ? 0 : PL.dur(T)).ease(d3.easeCubicInOut);
    const h0 = H0 == null || W0 !== W ? H : H0;
    svg.attr("viewBox", `0 0 ${W} ${h0}`);
    t.attrTween("viewBox", () => tt => `0 0 ${W} ${h0 + (H - h0) * tt}`);
    H0 = H; W0 = W;
    gAxis.transition(t).attr("transform", `translate(0,${H - m.b + 4})`)
      .call(d3.axisBottom(x).tickValues(small ? [0, 16, 32, 52] : [0, 8, 16, 24, 32, 40, 52]).tickSize(-(H - m.t - m.b + 4)))
      .on("end", () => gAxis.selectAll(".tick line").attr("stroke", "var(--rule)"));
    gAxis.selectAll(".tick line").attr("stroke", "var(--rule)");
    gAxis.select(".domain").remove();
    gAxis.selectAll("text").attr("fill", "var(--ink)").attr("font-size", 12);
    xLabel.attr("x", x(26)).attr("text-anchor", "middle").attr("fill", "var(--ink)").attr("font-size", 12)
      .text(small ? `weeks, ${PL.parentName(state.parent)}${state.disc ? " (with discretionary)" : ""}`
        : `weeks of paid leave or relief, ${PL.parentName(state.parent)}${state.disc ? ", with discretionary benefits" : ""}`)
      .transition(t).attr("y", H - 4);
    // group labels and medians: fade the old out and the new in
    gRows.selectAll("g.row").interrupt().transition().duration(PL.dur(T / 3)).style("opacity", 0).remove();
    const placed = [];
    rowsG.forEach((row, i) => {
      const cy = m.t + i * rowH + rowH / 2, med = PL.median(row.pts.map(p => p.v));
      const r = gRows.append("g").attr("class", "row").style("opacity", 0);
      r.append("text").attr("x", m.l - 10).attr("y", cy - 2).attr("text-anchor", "end").attr("fill", "var(--ink)").attr("font-size", small ? 12 : 13).text(row.name);
      r.append("text").attr("x", m.l - 10).attr("y", cy + 14).attr("text-anchor", "end").attr("fill", "var(--muted)").attr("font-size", 11)
        .text(`${row.pts.length} · median ${PL.fmt(med)}`);
      if (med != null) r.append("line").attr("x1", x(med)).attr("x2", x(med)).attr("y1", cy - rowH / 2 + 5).attr("y2", cy + rowH / 2 - 5)
        .attr("stroke", "var(--ink)").attr("stroke-width", 2);
      r.transition().delay(PL.dur(T / 3)).duration(PL.dur(T)).style("opacity", 1);
      placed.push(...swarm(row.pts, cy, rowH / 2 - 4));
    });
    gDots.selectAll("circle.dot").data(placed, p => p.d.institution_id)
      .join(enter => enter.append("circle").attr("class", "dot").attr("r", R).attr("cx", p => p.px).attr("cy", p => p.py).style("opacity", 0),
            update => update, exit => exit.transition(t).style("opacity", 0).remove())
      .attr("stroke", "#fff").attr("stroke-width", 0.7).style("cursor", opts.onPick ? "pointer" : "default")
      .on("mouseenter mousemove", (e, p) => tip.show(e, `<b>${p.d.institution}</b><br>${PL.fmt(p.v)} weeks${p.d[rc] ? ` (${p.d[rc]})` : ""}` +
        (state.group === "limits" && limits.get(p.d.institution_id).text ? `<br>limits on use: ${limits.get(p.d.institution_id).text}` : "") +
        (p.v > 53 ? "<br>(drawn at the right edge)" : "") + (opts.onPick ? "<br><i>click to see the policy</i>" : "")))
      .on("mouseleave", () => tip.hide())
      .on("click", (e, p) => opts.onPick && opts.onPick(p.d.institution_id, state.parent))
      .transition(t).attr("cx", p => p.px).attr("cy", p => p.py).style("opacity", 0.88);
    highlight();
    // the text alternative: each group's size and median, for the current parent and benefits counted
    summaryText = `${g.label === "all institutions" ? "All institutions" : `Grouped by ${g.label}`}, ${PL.parentName(state.parent)}, ` +
      `${state.disc ? "with discretionary benefits" : "guaranteed benefits"}: ` +
      rowsG.map(r => `${r.name}, ${r.pts.length} institutions, median ${PL.fmt(PL.median(r.pts.map(p => p.v)))} weeks`).join("; ") + ".";
    summary(summaryText);
  }
  draw();
  PL.onResize(chart.node(), () => draw(true));
  return { set(s) { Object.assign(state, s); draw(); root.scrollIntoView({ behavior: PL.scrollBehavior(), block: "start" }); } };
}
