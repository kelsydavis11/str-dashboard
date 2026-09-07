"""Monthly booking calendar + performance KPIs — calm premium dashboard.

Full-cell reservation chips (grid-column span over occupied nights), property
colour = brand accent (Surry Hills sage-deep, Darlinghurst terracotta). KPIs are
restrained: strong value, quiet label, one supporting detail (occupancy keeps a
thin target track; revenue/ADR carry a compact delta; the rest a single
footnote). Read-only; no upstream changes.
"""
from __future__ import annotations

import html
from urllib.parse import quote

import pandas as pd
import streamlit as st

import metrics as m
from theme import THEME

PROPERTIES = list(THEME["props"].keys())
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY = pd.Timedelta(days=1)
BAR_PITCH = 25
TARGET_OCC = 0.85

CAL_CSS = """
<style>
.kstrip { display:grid; grid-template-columns:repeat(6,1fr); background:var(--surface); border:1px solid var(--rule); border-radius:4px; overflow:hidden; margin:0 0 30px; }
.kc { padding:18px 22px; display:flex; flex-direction:column; gap:9px; border-left:1px solid var(--rule-soft); min-height:104px; }
.kc:first-child { border-left:none; }
.kl { font-size:11px; font-weight:500; letter-spacing:.02em; color:var(--ink-soft); }
.krow { display:flex; align-items:baseline; gap:9px; }
.kv { font-size:29px; font-weight:400; letter-spacing:-.02em; line-height:1; color:var(--ink); font-variant-numeric:tabular-nums; }
.kv .u { font-size:15px; color:var(--ink-soft); }
.kv.warn { color:var(--warn); }
.kf { font-size:11.5px; color:var(--ink-soft); margin-top:auto; line-height:1.4; }
.kf.pos { color:var(--pos); } .kf.neg { color:var(--neg); }
.delta { font-size:12.5px; font-weight:500; font-variant-numeric:tabular-nums; }
.delta.pos { color:var(--pos); } .delta.neg { color:var(--neg); } .delta.flat { color:var(--ink-soft); }
.track { position:relative; height:3px; background:var(--bg-sunken); border-radius:2px; }
.track i { display:block; height:100%; background:var(--sage-deep); border-radius:2px; }
.track b { position:absolute; top:-1.5px; width:1.5px; height:6px; background:var(--ink-soft); }
@media (max-width:1100px){ .kstrip { grid-template-columns:repeat(3,1fr); } .kc { border-top:1px solid var(--rule-soft); } }
.cal-tb { display:flex; align-items:baseline; justify-content:space-between; margin:0 2px 16px; flex-wrap:wrap; gap:12px; }
.cal-tbl { display:flex; align-items:baseline; gap:14px; }
.cal-month { font-size:17px; font-weight:500; color:var(--ink); }
.cal-todaytxt { font-size:12px; color:var(--ink-soft); }
.cal-tbr { display:flex; align-items:center; gap:20px; }
.cal-legend { display:flex; align-items:center; gap:15px; font-size:11.5px; color:var(--ink-soft); }
.cal-legend span { display:inline-flex; align-items:center; gap:6px; }
.lg-book { width:15px; height:9px; border-radius:2px; background:rgba(82,96,77,.16); }
.lg-vac { width:13px; height:9px; border-radius:2px; background:#FBF3E2; background-image:repeating-linear-gradient(135deg,transparent 0 3px,rgba(166,124,46,.35) 3px 4px); }
.lg-turn { width:7px; height:7px; background:var(--warn); transform:rotate(45deg); }
.cal-tools { display:flex; align-items:center; gap:6px; }
.cal-tools a { height:28px; box-sizing:border-box; display:inline-flex; align-items:center; text-decoration:none; color:var(--ink); border:1px solid var(--rule); background:var(--surface); border-radius:3px; font-weight:400; font-size:12px; }
.cal-tools a:hover { background:var(--bg-sunken); }
.cal-tools .ico { padding:0 10px; color:var(--ink-soft); }
.cal-tools .today, .cal-tools .toggle { padding:0 12px; }
.cal-tools .toggle { color:var(--ink-soft); }
.cal-tools .toggle.on { color:var(--sage-deep); border-color:var(--sage-deep); background:var(--sage-tint); }
.cal-wrap { display:grid; grid-template-columns:1fr 1fr; gap:22px; }
@media (max-width:1000px){ .cal-wrap { grid-template-columns:1fr; } }
.cal-panel { background:var(--surface); border:1px solid var(--rule); border-radius:4px; padding:16px 16px 14px; }
.cal-phead { display:flex; align-items:center; justify-content:space-between; min-height:24px; margin:0 2px 12px; }
.cal-pname { display:flex; align-items:center; gap:8px; font-size:14px; font-weight:500; letter-spacing:0; }
.cal-dot { width:8px; height:8px; border-radius:999px; flex:none; }
.cal-pkpi { display:flex; gap:14px; font-size:12.5px; color:var(--ink-mid); font-variant-numeric:tabular-nums; }
.cal-pkpi .pl { font-size:11px; color:var(--ink-soft); margin-right:4px; }
.cal-pkpi b { font-weight:500; color:var(--ink); }
.cal-dow { display:grid; grid-template-columns:repeat(7,1fr); margin-bottom:3px; }
.cal-dow span { text-align:left; padding-left:6px; font-size:11px; font-weight:400; color:var(--ink-soft); padding-bottom:6px; }
.cal-week { position:relative; }
.cal-bg { display:grid; grid-template-columns:repeat(7,1fr); }
.cal-cell { border-top:1px solid var(--rule-soft); border-left:1px solid var(--rule-soft); padding:5px 7px; }
.cal-cell:nth-child(7n) { border-right:1px solid var(--rule-soft); }
.cal-week:last-child .cal-cell { border-bottom:1px solid var(--rule-soft); }
.cal-cell.we { background:#F7F8FA; }
.cal-cell.out { background:#F1F2F4; }
.cal-cell.vac { background-color:#FCF6EA; background-image:repeating-linear-gradient(135deg,transparent 0 4px,rgba(166,124,46,.18) 4px 5px); }
.cal-cell.todaycell { box-shadow:inset 0 0 0 1.5px var(--ink); }
.cal-cellhead { display:flex; align-items:center; justify-content:space-between; height:15px; }
.cal-daynum { font-size:11px; font-weight:400; color:var(--ink-soft); font-variant-numeric:tabular-nums; }
.cal-cell.out .cal-daynum { color:#C2BEB7; }
.diamond { width:6px; height:6px; background:var(--warn); transform:rotate(45deg); }
.cal-bars { position:absolute; top:23px; left:0; right:0; bottom:4px; display:grid; grid-template-columns:repeat(7,1fr); grid-auto-rows:20px; row-gap:4px; pointer-events:none; }
.pill { pointer-events:auto; text-decoration:none !important; display:flex; align-items:center; height:20px; margin:0 3px; padding:0 8px; border-radius:3px; font-size:11.5px; font-weight:400; white-space:nowrap; overflow:hidden; transition:filter .12s; }
.pill:hover { filter:brightness(.97); z-index:3; }
.pill .nm { overflow:hidden; text-overflow:ellipsis; }
.pill .amt { margin-left:auto; padding-left:8px; font-weight:500; font-variant-numeric:tabular-nums; }
.pill.cl { border-top-left-radius:0; border-bottom-left-radius:0; margin-left:0; }
.pill.cr { border-top-right-radius:0; border-bottom-right-radius:0; margin-right:0; }
.pill.current { box-shadow:inset 0 0 0 1.5px currentColor; }
.pill.cancelled { background:#EEEDE9 !important; color:#9A958E !important; }
.pill.cancelled .nm { text-decoration:line-through; }
.cal-foot { display:flex; justify-content:space-between; margin:12px 2px 0; font-size:11.5px; color:var(--ink-soft); }
.cal-foot b { color:var(--ink-mid); font-weight:500; }
.cal-detail { background:var(--surface); border:1px solid var(--rule); border-radius:4px; padding:18px 20px; margin-top:18px; }
.cal-detail .dh { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
.cal-detail .dt { font-size:16px; font-weight:500; }
.cal-detail .x { text-decoration:none; color:var(--ink-soft); border:1px solid var(--rule); border-radius:3px; padding:3px 10px; font-size:12px; }
.cal-detail .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(135px,1fr)); gap:14px 26px; }
.cal-detail .f .l { font-size:11px; font-weight:400; color:var(--ink-soft); }
.cal-detail .f .val { font-size:14px; font-weight:400; margin-top:3px; font-variant-numeric:tabular-nums; }
.cal-tag { display:inline-block; font-size:11.5px; font-weight:400; padding:2px 9px; border-radius:3px; background:var(--bg-sunken); color:var(--ink-mid); }
.ag { background:var(--surface); border:1px solid var(--rule); border-radius:8px; margin-top:28px; overflow:hidden; }
.ag-head { display:flex; align-items:baseline; justify-content:space-between; padding:14px 18px; border-bottom:1px solid var(--rule); }
.ag-head .t { font-size:14px; font-weight:600; color:var(--ink); }
.ag-head .c { font-size:12px; color:var(--ink-soft); }
.ag-now { display:flex; flex-wrap:wrap; align-items:center; gap:8px 16px; padding:11px 18px; background:var(--bg-sunken); border-bottom:1px solid var(--rule); font-size:12.5px; color:var(--ink-mid); }
.ag-now .lbl { font-size:12px; font-weight:600; color:var(--ink); }
.ag-now .now-item { display:inline-flex; align-items:center; gap:6px; }
.ag-now .now-item .dot { width:7px; height:7px; border-radius:999px; flex:none; }
.ag-now .now-empty { color:var(--ink-soft); }
.ag-day { display:grid; grid-template-columns:148px 1fr; gap:16px; padding:13px 18px; border-bottom:1px solid var(--rule-soft); }
.ag-day:last-child { border-bottom:none; }
.ag-day.is-today { background:#FAFBFC; }
.ag-daylabel { display:flex; flex-direction:column; gap:2px; }
.ag-daylabel .rel { font-size:13px; font-weight:600; color:var(--ink); }
.ag-daylabel .rel.today { color:var(--sage-deep); }
.ag-daylabel .abs { font-size:12px; color:var(--ink-soft); font-variant-numeric:tabular-nums; }
.ag-rows { display:flex; flex-direction:column; gap:9px; }
.ag-ev { display:flex; align-items:center; gap:12px; text-decoration:none !important; color:var(--ink); font-size:13px; }
.ag-ev:hover .ev-body { color:var(--sage-deep); }
.ev-tag { flex:none; width:82px; text-align:center; font-size:11px; font-weight:600; padding:3px 0; border-radius:4px; }
.ev-tag.checkin { background:var(--sage-tint); color:var(--sage-deep); }
.ev-tag.checkout { background:var(--bg-sunken); color:var(--ink-mid); }
.ev-tag.turnover { background:#F6E9CC; color:#8A6318; }
.ev-body { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ev-body b { font-weight:600; }
.ev-meta { flex:none; color:var(--ink-soft); font-size:12px; }
.ag-none { font-size:12.5px; color:var(--ink-soft); }
@media (max-width:760px){ .ag-day { grid-template-columns:1fr; gap:6px; } }
</style>
"""

def _money(v) -> str:
    return f"${v:,.0f}" if pd.notna(v) else ""

def _money_k(v) -> str:
    if pd.isna(v):
        return "$0"
    return f"${v/1000:.1f}k" if abs(v) >= 1000 else f"${v:.0f}"

def _delta(cur, prev) -> str:
    if prev is None or pd.isna(prev) or prev <= 0:
        return '<span class="delta flat">–</span>'
    pct = (cur - prev) / prev * 100
    if pct >= 0:
        return f'<span class="delta pos">▲ {pct:.0f}%</span>'
    return f'<span class="delta neg">▼ {abs(pct):.0f}%</span>'

def _month_from_query(today):
    ym = st.query_params.get("ym")
    if ym:
        try:
            return pd.Timestamp(ym + "-01").normalize()
        except Exception:
            pass
    return today.replace(day=1)

def _weeks(month_start):
    last = (month_start + pd.offsets.MonthEnd(0)).normalize()
    grid_start = month_start - pd.Timedelta(days=month_start.weekday())
    grid_end = last + pd.Timedelta(days=6 - last.weekday())
    weeks, d = [], grid_start
    while d <= grid_end:
        weeks.append([d + pd.Timedelta(days=i) for i in range(7)])
        d += pd.Timedelta(days=7)
    return weeks

def weeks_month(weeks):
    return weeks[2][3].month

def _prep_bookings(df, prop_key, show_cancelled):
    sub = df[df["property_raw"] == prop_key]
    out = []
    for _, r in sub.iterrows():
        if pd.isna(r["check_in"]) or pd.isna(r["check_out"]) or r["check_out"] <= r["check_in"]:
            continue
        if r["is_cancelled"] and not show_cancelled:
            continue
        name = str(r.get("guest") or "").strip()
        out.append({
            "id": r["booking_id"], "platform": r["platform"],
            "short": name.split()[0] if name else "Guest",
            "net": r["revenue_net"], "cancelled": bool(r["is_cancelled"]),
            "first_night": r["check_in"].normalize(),
            "last_night": (r["check_out"] - DAY).normalize(),
        })
    return out

def _month_facts(bookings, month_start, target_month, days_in_month):
    active = [b for b in bookings if not b["cancelled"]]
    occupied = set()
    for b in active:
        d = b["first_night"]
        while d <= b["last_night"]:
            if d.month == target_month:
                occupied.add(d)
            d += DAY
    checkins = {b["first_night"] for b in active if b["first_night"].month == target_month}
    checkouts = {b["last_night"] + DAY for b in active if (b["last_night"] + DAY).month == target_month}
    turns = checkins & checkouts
    changeover_days = len(checkins | checkouts)
    month_days = [month_start + pd.Timedelta(days=i) for i in range(days_in_month)]
    vacant = [d for d in month_days if d not in occupied]
    return occupied, vacant, turns, changeover_days

def _segments_for_week(week, bookings, today):
    w0, w6 = week[0], week[6]
    segs = []
    for b in bookings:
        if b["last_night"] < w0 or b["first_night"] > w6:
            continue
        s = max(b["first_night"], w0)
        e = min(b["last_night"], w6)
        segs.append({
            "start": (s - w0).days, "span": (e - s).days + 1,
            "cont_left": b["first_night"] < s, "cont_right": b["last_night"] > e,
            "current": b["first_night"] <= today <= b["last_night"], "b": b,
        })
    segs.sort(key=lambda x: (x["start"], -x["span"]))
    lane_end = []
    for seg in segs:
        placed = False
        for i, end in enumerate(lane_end):
            if seg["start"] > end:
                seg["lane"] = i
                lane_end[i] = seg["start"] + seg["span"] - 1
                placed = True
                break
        if not placed:
            seg["lane"] = len(lane_end)
            lane_end.append(seg["start"] + seg["span"] - 1)
    return segs

def _pill_html(seg, ym, suffix, colors) -> str:
    b = seg["b"]
    span = seg["span"]
    cls = ["pill"]
    if b["cancelled"]: cls.append("cancelled")
    if seg["current"] and not b["cancelled"]: cls.append("current")
    if seg["cont_left"]: cls.append("cl")
    if seg["cont_right"]: cls.append("cr")
    name = html.escape(str(b["short"]))
    amt = _money(b["net"])
    amt_html = f'<span class="amt">{amt}</span>' if (amt and span >= 2) else ""
    href = f"?ym={ym}&booking={quote(str(b['id']))}{suffix}"
    style = (f"grid-column:{seg['start']+1}/span {span};grid-row:{seg['lane']+1};"
             f"background:{colors['chip']};color:{colors['base']};")
    return (f'<a class="{" ".join(cls)}" style="{style}" href="{href}" target="_self">'
            f'<span class="nm">{name}</span>{amt_html}</a>')

def _panel_html(prop_key, bookings, weeks, today, ym, suffix, occupied, turns, kpi) -> str:
    target_month = weeks_month(weeks)
    colors = THEME["props"][prop_key]
    parts = [f'<div class="cal-panel"><div class="cal-phead"><div class="cal-pname" style="color:{colors["base"]}"><span class="cal-dot" style="background:{colors["base"]}"></span>{html.escape(colors["short"])}</div><div class="cal-pkpi">{kpi}</div></div>']
    parts.append('<div class="cal-dow">' + "".join(f"<span>{d}</span>" for d in DOW) + "</div>")
    for week in weeks:
        segs = _segments_for_week(week, bookings, today)
        nlanes = max((s["lane"] for s in segs), default=-1) + 1
        cell_h = max(70, 26 + nlanes * BAR_PITCH)
        cells = []
        for d in week:
            in_month = d.month == target_month
            classes = ["cal-cell"]
            title = ""
            if d == today: classes.append("todaycell")
            elif not in_month: classes.append("out")
            elif d not in occupied:
                classes.append("vac"); title = ' title="Available"'
            elif d.weekday() >= 5: classes.append("we")
            diamond = ('<span class="diamond" title="Same-day turnover"></span>' if d in turns and in_month else "")
            cells.append(f'<div class="{" ".join(classes)}"{title} style="min-height:{cell_h}px"><div class="cal-cellhead"><span class="cal-daynum">{d.day}</span>{diamond}</div></div>')
        bars = "".join(_pill_html(s, ym, suffix, colors) for s in segs)
        parts.append(f'<div class="cal-week"><div class="cal-bg">{"".join(cells)}</div><div class="cal-bars">{bars}</div></div>')
    parts.append("</div>")
    return "".join(parts)

def _detail_card(df, booking_id, ym, suffix):
    row = df[df["booking_id"].astype(str) == str(booking_id)]
    if row.empty: return
    r = row.iloc[0]
    d = lambda x: x.strftime("%d %b %Y") if pd.notna(x) else "—"
    nights = int(r["los"]) if pd.notna(r["los"]) else "—"
    nightly = (r["revenue_net"] / r["los"]) if (pd.notna(r["revenue_net"]) and pd.notna(r["los"]) and r["los"]) else float("nan")
    guests = int(r["guests"]) if pd.notna(r["guests"]) else "—"
    lead = f'{int(r["lead_time_days"])} d' if pd.notna(r["lead_time_days"]) else "—"
    def f(label, val):
        return f'<div class="f"><div class="l">{label}</div><div class="val">{val}</div></div>'
    fields = "".join([
        f("Guest", html.escape(str(r.get("guest") or "—"))), f("Property", html.escape(str(r["property"]))),
        f("Platform", f'<span class="cal-tag">{html.escape(str(r["platform"]))}</span>'),
        f("Booking ID", html.escape(str(r["booking_id"]))), f("Check-in", d(r["check_in"])), f("Check-out", d(r["check_out"])),
        f("Nights", nights), f("Guests", guests), f("Booked on", d(r["booked_on"])), f("Lead time", lead),
        f("Net payout", _money(r["revenue_net"]) or "—"), f("Nightly rate", _money(nightly) or "—"), f("Status", html.escape(str(r["status"]))),
    ])
    st.markdown(f'<div class="cal-detail"><div class="dh"><span class="dt">{html.escape(str(r.get("guest") or "Reservation"))}</span><a class="x" href="?ym={ym}{suffix}" target="_self">✕ close</a></div><div class="grid">{fields}</div></div>', unsafe_allow_html=True)

def _nights(r):
    return int(r["los"]) if pd.notna(r["los"]) else None

def _agenda(df, today, ym, suffix):
    props = THEME["props"]
    def prop(pk): return props.get(pk, {"base": "#787E88", "short": str(pk)})
    a = df[df["property_raw"].isin(PROPERTIES) & (~df["is_cancelled"]) & df["usable"]].copy()
    ci = a["check_in"].dt.normalize(); co = a["check_out"].dt.normalize()
    now = a[(ci <= today) & (co > today)].sort_values("check_out")
    now_items = []
    for _, r in now.iterrows():
        c = prop(r["property_raw"]); d = r["check_out"].normalize()
        out = "today" if d == today else ("tomorrow" if d == today + DAY else f"{d:%a} {d.day}")
        now_items.append(f'<span class="now-item"><span class="dot" style="background:{c["base"]}"></span>{html.escape(str(r.get("guest") or "Guest"))} · {html.escape(c["short"])} · out {out}</span>')
    now_html = ('<div class="ag-now"><span class="lbl">In-house now</span>' + ("".join(now_items) if now_items else '<span class="now-empty">Both properties vacant</span>') + "</div>")
    def ev(typ, tag, body, bid, meta=""):
        href = f"?ym={ym}&booking={quote(str(bid))}{suffix}"
        meta_html = f'<span class="ev-meta">{meta}</span>' if meta else ""
        return f'<a class="ag-ev" href="{href}" target="_self"><span class="ev-tag {typ}">{tag}</span><span class="ev-body">{body}</span>{meta_html}</a>'
    day_blocks, event_count = [], 0
    for i in range(7):
        D = today + i * DAY
        deps = a[co == D]; arrs = a[ci == D]; evs = []
        for pk in PROPERTIES:
            c = prop(pk); dep = deps[deps["property_raw"] == pk]; arr = arrs[arrs["property_raw"] == pk]
            if len(dep) and len(arr):
                dg, ag = dep.iloc[0], arr.iloc[0]; n = _nights(ag)
                evs.append(ev("turnover", "Turnover", f'<b>{html.escape(c["short"])}</b> — {html.escape(str(dg.get("guest") or ""))} out → {html.escape(str(ag.get("guest") or ""))} in', ag["booking_id"], f'{n}-night stay' if n else ""))
            elif len(dep):
                dg = dep.iloc[0]; evs.append(ev("checkout", "Check-out", f'{html.escape(str(dg.get("guest") or ""))} · {html.escape(c["short"])}', dg["booking_id"]))
            elif len(arr):
                ag = arr.iloc[0]; n = _nights(ag); evs.append(ev("checkin", "Check-in", f'{html.escape(str(ag.get("guest") or ""))} · {html.escape(c["short"])}', ag["booking_id"], f'{n}-night stay' if n else ""))
        event_count += len(evs)
        if not evs and i > 1: continue
        rel = "Today" if i == 0 else ("Tomorrow" if i == 1 else "")
        rel_html = f'<span class="rel {"today" if i == 0 else ""}">{rel}</span>' if rel else ""
        rows = "".join(evs) if evs else '<div class="ag-none">No arrivals or departures</div>'
        day_blocks.append(f'<div class="ag-day{" is-today" if i == 0 else ""}"><div class="ag-daylabel">{rel_html}<span class="abs">{D:%a} {D.day} {D:%b}</span></div><div class="ag-rows">{rows}</div></div>')
    st.markdown(f'<div class="ag"><div class="ag-head"><span class="t">Next 7 days</span><span class="c">{event_count} arrival{"" if event_count == 1 else "s"} & departure{"" if event_count == 1 else "s"}</span></div>{now_html}{"".join(day_blocks)}</div>', unsafe_allow_html=True)

def render(df, today, period_start=None):
    st.markdown(CAL_CSS, unsafe_allow_html=True)
    period_month = (pd.Timestamp(period_start).replace(day=1).normalize() if period_start is not None else today.replace(day=1))
    period_ym = f"{period_month.year:04d}-{period_month.month:02d}"
    if st.session_state.get("_cal_period") != period_ym:
        st.session_state["_cal_period"] = period_ym
        st.query_params["ym"] = period_ym
        month_start = period_month
    else:
        q = st.query_params.get("ym")
        try: month_start = pd.Timestamp((q or period_ym) + "-01").normalize()
        except Exception: month_start = period_month
    ym = f"{month_start.year:04d}-{month_start.month:02d}"
    show_cancelled = st.query_params.get("cx") == "1"
    suffix = "&cx=1" if show_cancelled else ""
    month_end = month_start + pd.offsets.MonthEnd(0) + pd.Timedelta(days=1)
    days_in_month = (month_end - month_start).days
    target_month = month_start.month
    weeks = _weeks(month_start)
    both = df[df["property_raw"].isin(PROPERTIES)]
    combined = m.period_summary(both, month_start, month_end, units=2)
    per = {}; booked_total = vac_total = turn_total = vac_weekend = changeover_total = 0
    for pk in PROPERTIES:
        bk = _prep_bookings(df, pk, show_cancelled)
        occ, vac, turns, chg = _month_facts(bk, month_start, target_month, days_in_month)
        s = m.period_summary(df[df["property_raw"] == pk], month_start, month_end, units=1)
        per[pk] = {"bk": bk, "occ": occ, "vac": vac, "turns": turns, "s": s}
        booked_total += len(occ); vac_total += len(vac); turn_total += len(turns); changeover_total += chg
        vac_weekend += sum(1 for dv in vac if dv.weekday() >= 4)
    available = 2 * days_in_month
    occ_pct = booked_total / available if available else 0
    pts = (occ_pct - TARGET_OCC) * 100
    prev_start = month_start - pd.DateOffset(months=1)
    prev = m.period_summary(both, prev_start, month_start, units=2)
    net_prev, adr_prev = prev["net_revenue"], prev["adr_net"]
    wk_rev = wk_n = wd_rev = wd_n = 0.0
    for pk in PROPERTIES:
        for b in per[pk]["bk"]:
            if b["cancelled"] or pd.isna(b["net"]): continue
            los = (b["last_night"] - b["first_night"]).days + 1
            nightly = b["net"] / los if los else 0
            d = b["first_night"]
            while d <= b["last_night"]:
                if d.month == target_month:
                    if d.weekday() >= 4: wk_rev += nightly; wk_n += 1
                    else: wd_rev += nightly; wd_n += 1
                d += DAY
    wknd_adr = wk_rev / wk_n if wk_n else float("nan")
    wkdy_adr = wd_rev / wd_n if wd_n else float("nan")
    vac_mid = vac_total - vac_weekend
    net_foot = (f"vs {_money_k(net_prev)} in {prev_start:%B}" if net_prev > 0 else f"no {prev_start:%B} data")
    occ_cls = "pos" if pts >= 0 else "neg"
    occ_foot = f'{abs(pts):.0f} pts {"above" if pts >= 0 else "below"} {TARGET_OCC*100:.0f}% target'
    strip = "".join([
        f'<div class="kc"><div class="kl">Occupancy</div><div class="krow"><span class="kv">{occ_pct*100:.0f}%</span></div><div class="track"><i style="width:{min(occ_pct*100,100):.0f}%"></i><b style="left:{TARGET_OCC*100:.0f}%"></b></div><div class="kf {occ_cls}">{occ_foot}</div></div>',
        f'<div class="kc"><div class="kl">Booked nights</div><div class="krow"><span class="kv">{booked_total}<span class="u"> / {available}</span></span></div><div class="kf">{vac_total} night{"" if vac_total == 1 else "s"} unsold</div></div>',
        f'<div class="kc"><div class="kl">Net revenue</div><div class="krow"><span class="kv">{_money_k(combined["net_revenue"])}</span>{_delta(combined["net_revenue"], net_prev)}</div><div class="kf">{net_foot}</div></div>',
        f'<div class="kc"><div class="kl">ADR</div><div class="krow"><span class="kv">{_money(combined["adr_net"]) or "—"}</span>{_delta(combined["adr_net"], adr_prev)}</div><div class="kf">Wkdy {_money(wkdy_adr) or "—"} · Wknd {_money(wknd_adr) or "—"}</div></div>',
        f'<div class="kc"><div class="kl">Vacant nights</div><div class="krow"><span class="kv warn">{vac_total}</span></div><div class="kf">{vac_weekend} on Fri–Sat · {vac_mid} midweek</div></div>',
        f'<div class="kc"><div class="kl">Turnovers</div><div class="krow"><span class="kv">{turn_total}</span></div><div class="kf">of {changeover_total} changeover days</div></div>',
    ])
    st.markdown(f'<div class="kstrip">{strip}</div>', unsafe_allow_html=True)
    prev_ym = (month_start - pd.DateOffset(months=1)).strftime("%Y-%m")
    next_ym = (month_start + pd.DateOffset(months=1)).strftime("%Y-%m")
    cur_ym = today.strftime("%Y-%m")
    toggle_href = f"?ym={ym}" + ("" if show_cancelled else "&cx=1")
    toggle_cls = "toggle on" if show_cancelled else "toggle"
    toggle_lbl = ("☑ " if show_cancelled else "☐ ") + "Cancelled"
    today_txt = (f'Today is {today:%A} {today.day} {today:%B}' if month_start.month == today.month and month_start.year == today.year else "")
    st.markdown(f'<div class="cal-tb"><div class="cal-tbl"><span class="cal-month">{month_start:%B %Y}</span><span class="cal-todaytxt">{today_txt}</span></div><div class="cal-tbr"><div class="cal-legend"><span><i class="lg-book"></i> Booked</span><span><i class="lg-vac"></i> Vacant</span><span><i class="lg-turn"></i> Turnover</span></div><div class="cal-tools"><a class="ico" href="?ym={prev_ym}{suffix}" target="_self">‹</a><a class="today" href="?ym={cur_ym}{suffix}" target="_self">Today</a><a class="ico" href="?ym={next_ym}{suffix}" target="_self">›</a><a class="{toggle_cls}" href="{toggle_href}" target="_self">{toggle_lbl}</a></div></div></div>', unsafe_allow_html=True)
    panels = []
    for pk in PROPERTIES:
        s = per[pk]["s"]
        netk = _money_k(s["net_revenue"]).replace("k", "K")
        kpi = (f'<span><span class="pl">Occ</span><b>{s["occupancy"]*100:.0f}%</b></span><span><b>{netk}</b></span><span><span class="pl">ADR</span><b>{_money(s["adr_net"]) or "—"}</b></span>')
        panels.append(_panel_html(pk, per[pk]["bk"], weeks, today, ym, suffix, per[pk]["occ"], per[pk]["turns"], kpi))
    st.markdown('<div class="cal-wrap">' + "".join(panels) + "</div>", unsafe_allow_html=True)
    fcols = st.columns(len(PROPERTIES), gap="medium")
    for col, pk in zip(fcols, PROPERTIES):
        p = per[pk]; dates = ", ".join(str(d.day) for d in p["vac"])
        col.markdown(f'<div class="cal-foot"><span><b>{len(p["vac"])} vacant nights</b>{(" · " + dates) if dates else ""}</span><span>{len(p["turns"])} turnovers</span></div>', unsafe_allow_html=True)
    _agenda(df, today, ym, suffix)
    selected = st.query_params.get("booking")
    if selected:
        _detail_card(df, selected, ym, suffix)
