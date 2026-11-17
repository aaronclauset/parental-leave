// Graphic 3: the primary value against prestige rank (U.S. institutions), with a moving average,
// an optional moving average of the v1 values, and AAU members highlighted on request.
function Prestige(sel, rows, diffs) {
  const root = document.querySelector(sel);
  const state = { parent: "birth", disc: false, v1: false, aau: false };
  const v1 = new Map(diffs.map(d => [d.institution_id, d]));
  const data = rows.filter(d => d.country === "US" && d.prestige_rank != null && d.values_available === "yes");
  const controls = d3.select(root).append("div").attr("class", "controls");
  const refreshers = [
    PL.seg(controls.node(), [["birth", "birth parent"], ["nonbirth", "non-birth parent"]], () => state.parent, v => { state.parent = v; draw(); }, "parent"),
    PL.seg(controls.node(), [[false, "guaranteed"], [true, "with discretionary"]], () => state.disc, v => { state.disc = v; draw(); }, "benefits counted"),
  ];
  const chk = (key, label) => controls.append("label").attr("class", "chk").call(l => {
    l.append("input").attr("type", "checkbox").on("change", e => { state[key] = e.target.checked; draw(); });
    l.append("span").text(label);
  });
  chk("aau", "highlight AAU members");
  chk("v1", "show v1 (moving average)");
  const chart = d3.select(root).append("div").attr("class", "chart");
  const svg = chart.append("svg").attr("role", "img").attr("aria-label", "Weeks of paid leave or relief against prestige rank");
  const tip = PL.tipper(chart.node());
  const summary = PL.describe(svg, `${root.id}-summary`);
  const H = 400, m = { l: 52, r: 16, t: 14, b: 44 }, WIN = 25;
  let W = 900;
  const x = d3.scaleLinear().domain([0, d3.max(data, d => d.prestige_rank) + 5]);
  const y = d3.scaleLinear().domain([0, 54]).range([H - m.b, m.t]);
  function moving(pts) {  // centered moving average over WIN institutions in rank order
    const s = pts.filter(p => p.v != null).sort((a, b) => a.r - b.r), h = Math.floor(WIN / 2), out = [];
    for (let i = h; i < s.length - h; i++) out.push([s[i].r, d3.mean(s.slice(i - h, i + h + 1), p => p.v)]);
    return out;
  }
  // the axes and legend are redrawn when the width changes; points and lines move to their new places
  const T = 600;
  const gX = svg.append("g").attr("transform", `translate(0,${H - m.b})`);
  svg.append("g").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).tickValues([0, 8, 16, 24, 32, 40, 52]))
    .call(a => a.selectAll("text").attr("fill", "var(--ink)").attr("font-size", 12));
  const xLabel = svg.append("text").attr("y", H - 6).attr("text-anchor", "middle").attr("font-size", 12).attr("fill", "var(--ink)");
  const yLabel = svg.append("text").attr("transform", `translate(14,${(H - m.b + m.t) / 2}) rotate(-90)`).attr("text-anchor", "middle")
    .attr("font-size", 12).attr("fill", "var(--ink)");
  const gPts = svg.append("g"), avgLine = svg.append("path").attr("fill", "none").attr("stroke", "var(--accent)").attr("stroke-width", 2.4);
  const v1Line = svg.append("path").attr("fill", "none").attr("stroke", "var(--ink)").attr("stroke-width", 1.6).attr("stroke-dasharray", "5 4")
    .style("opacity", 0);
  const lg = svg.append("g").attr("font-size", 12).attr("fill", "var(--ink)");
  lg.append("line").attr("x2", 26).attr("stroke", "var(--accent)").attr("stroke-width", 2.4);
  lg.append("text").attr("x", 32).attr("y", 4).text(`v2.0, moving average of ${WIN}`);
  const lgV1 = lg.append("g").style("opacity", 0);
  lgV1.append("line").attr("y1", 18).attr("y2", 18).attr("x2", 26).attr("stroke", "var(--ink)").attr("stroke-width", 1.6).attr("stroke-dasharray", "5 4");
  lgV1.append("text").attr("x", 32).attr("y", 22).text("v1.0, moving average");
  const line = d3.line().x(p => x(p[0])).y(p => y(p[1]));
  let first = true;
  function draw(instant = false) {
    refreshers.forEach(f => f());
    W = PL.chartWidth(chart.node(), 900);
    const small = PL.narrow(W);
    x.range([m.l, W - m.r]);
    svg.attr("viewBox", `0 0 ${W} ${H}`);
    gX.call(d3.axisBottom(x).ticks(small ? 4 : 8)).call(a => a.selectAll("text").attr("fill", "var(--ink)").attr("font-size", 12));
    xLabel.attr("x", (m.l + W - m.r) / 2).text(small ? "prestige rank (1 = most prestigious)" : "prestige rank (1 = most prestigious; Wapman et al. 2022)");
    lg.attr("transform", `translate(${small ? m.l + 10 : W - m.r - 250},${m.t + 6})`);
    const c = PL.col(state.parent, state.disc);
    const pts = data.map(d => ({ d, r: d.prestige_rank, v: d[c] }));
    const t = svg.transition().duration(first || instant ? 0 : PL.dur(T)).ease(d3.easeCubicInOut);
    first = false;
    yLabel.text(`weeks, ${PL.parentName(state.parent)}`);
    gPts.selectAll("circle").data(pts.filter(p => p.v != null), p => p.d.institution_id)
      .join(enter => enter.append("circle").attr("cx", p => x(p.r)).attr("cy", p => y(Math.min(p.v, 53.5))).attr("r", 3.4)
        .attr("stroke", "#fff").attr("stroke-width", 0.7))
      .on("mouseenter mousemove", (e, p) => tip.show(e, `<b>${p.d.institution}</b><br>rank ${p.r}${p.d.aau_member_2018 ? " · AAU member" : ""}<br>${PL.fmt(p.v)} weeks`))
      .on("mouseleave", () => tip.hide())
      .transition(t).attr("cx", p => x(p.r)).attr("cy", p => y(Math.min(p.v, 53.5))).attr("r", p => (state.aau && p.d.aau_member_2018 ? 4.6 : 3.4))
      .attr("fill", p => (state.aau ? (p.d.aau_member_2018 ? "var(--accent)" : "var(--pale)") : "var(--gray)"));
    avgLine.raise().transition(t).attr("d", line(moving(pts)));
    const key = state.parent === "birth" ? "v1_birth_weeks" : "v1_nonbirth_weeks";
    const vpts = data.map(d => ({ r: d.prestige_rank, v: PL.num((v1.get(d.institution_id) || {})[key]) })).filter(p => Number.isFinite(p.v));
    if (!v1Line.attr("d")) v1Line.attr("d", line(moving(vpts)));
    v1Line.raise().transition(t).attr("d", line(moving(vpts))).style("opacity", state.v1 ? 1 : 0);
    lgV1.transition(t).style("opacity", state.v1 ? 1 : 0);
    // the text alternative: the moving average at the most and the least prestigious ends
    const avg = moving(pts), shown = pts.filter(p => p.v != null).length;
    summary(`Each point is one of ${shown} U.S. institutions: weeks for the ${PL.parentName(state.parent)}` +
      ` (${state.disc ? "with discretionary benefits" : "guaranteed"}) against prestige rank. The moving average of ${WIN} institutions is ` +
      `${PL.fmt(avg[0][1])} weeks at the most prestigious end and ${PL.fmt(avg[avg.length - 1][1])} weeks at the least prestigious end.` +
      (state.v1 ? ` For v1.0 it is ${PL.fmt(moving(vpts)[0][1])} and ${PL.fmt(moving(vpts).slice(-1)[0][1])} weeks.` : ""));
  }
  draw();
  PL.onResize(chart.node(), () => draw(true));
  return { set(s) { Object.assign(state, s); draw(); } };
}
