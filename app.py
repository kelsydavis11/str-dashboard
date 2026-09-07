"""STR management dashboard — Phase 1.

Read-only reporting over the 'Confirmed Bookings' tab. Reuses the existing
Booking.com-sync OAuth credentials. Does not modify the sheet or Apps Script.

Time model: a REPORTING PERIOD (real calendar window, default this month) drives
occupancy / revenue / ADR / RevPAR on an overlap + night-allocated basis — any
stay touching the window counts, regardless of its check-in date.
"""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

import calendar_view
import data as data_mod
import metrics as m
import theme

st.set_page_config(page_title="STR Dashboard", page_icon="🏠", layout="wide")
theme.register_theme()
st.markdown(theme.CSS, unsafe_allow_html=True)

TODAY = pd.Timestamp.today().normalize()
money = lambda x: f"${x:,.0f}" if pd.notna(x) else "—"
pct = lambda x: f"{x * 100:.1f}%" if pd.notna(x) else "—"
num = lambda x, d=0: f"{x:,.{d}f}" if pd.notna(x) else "—"
day = lambda x: x.strftime("%d %b %Y") if pd.notna(x) else "—"

@st.cache_data(ttl=600, show_spinner="Loading bookings…")
def load():
    return data_mod.load_bookings()

def cards(specs):
    cols = st.columns(len(specs))
    for col, (label, value, sub) in zip(cols, specs):
        col.markdown(theme.kpi_card(label, value, sub), unsafe_allow_html=True)

def bar(df, x, y, color=None, y_title="", fmt="$,.0f", scheme=None):
    enc = {
        "x": alt.X(f"{x}:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0, labelLimit=140)),
        "y": alt.Y(f"{y}:Q", title=y_title, axis=alt.Axis(format=fmt)),
        "tooltip": [x, alt.Tooltip(f"{y}:Q", format=fmt)],
    }
    if color:
        rng = scheme or (list(theme.PLATFORM_COLORS.values()) if color == "platform" else list(theme.PROPERTY_COLORS.values()))
        enc["color"] = alt.Color(f"{color}:N", legend=None, scale=alt.Scale(range=rng))
    return alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=46).encode(**enc).properties(height=280)

def month_bar(df, y, y_title, fmt, color=theme.ACCENT):
    return alt.Chart(df).mark_bar(size=32, cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=color).encode(
        x=alt.X("month:N", sort=list(df["month"]), title=None, axis=alt.Axis(labelAngle=-40)),
        y=alt.Y(f"{y}:Q", title=y_title, axis=alt.Axis(format=fmt)),
        tooltip=["month", alt.Tooltip(f"{y}:Q", format=fmt)],
    ).properties(height=300)

try:
    df, dq = load()
except Exception as exc:
    msg = str(exc).lower()
    if any(t in msg for t in ("invalid_grant", "expired or revoked", "refresh")):
        st.error("Google session expired — the saved token is no longer valid.")
        st.markdown("Re-authorise (opens a Google consent screen), then restart the app:\n\n```bash\ncd ~/booking-sync && node reauth-google.mjs\n```\n\nReuses the existing OAuth client and rewrites `token.json`.")
    else:
        st.error("Could not load the Google Sheet.")
        st.exception(exc)
    st.stop()

if df.empty:
    st.warning("No data returned from 'Confirmed Bookings'.")
    st.stop()

sb = st.sidebar
sb.header("Filters")
if sb.button("↻ Refresh data", use_container_width=True):
    load.clear()
    st.rerun()

props = sorted(df["property"].dropna().unique())
plats = sorted(df["platform"].dropna().unique())
sel_props = sb.multiselect("Property", props, default=props) or props
sel_plats = sb.multiselect("Platform", plats, default=plats) or plats
sel_status = sb.multiselect("Booking status", ["Booked", "Cancelled"], default=["Booked"])

month_start = TODAY.replace(day=1)
act_all = m.active(df)
data_start = act_all["check_in"].min().normalize() if not act_all.empty else TODAY
data_end = (act_all["check_out"].max().normalize() + pd.Timedelta(days=1) if not act_all.empty else TODAY + pd.Timedelta(days=1))
PRESETS = {
    "This month": (month_start, month_start + pd.DateOffset(months=1)),
    "Next 30 days": (TODAY, TODAY + pd.Timedelta(days=30)),
    "Next 3 months": (month_start, month_start + pd.DateOffset(months=3)),
    "Year to date": (TODAY.replace(month=1, day=1), TODAY + pd.Timedelta(days=1)),
    "Next 12 months": (month_start, month_start + pd.DateOffset(months=12)),
    "All time": (data_start, data_end),
    "Custom…": None,
}
choice = sb.selectbox("Reporting period", list(PRESETS), index=0)
if choice == "Custom…":
    c = sb.date_input("Custom range", value=(month_start.date(), (month_start + pd.DateOffset(months=1)).date()))
    if isinstance(c, (list, tuple)) and len(c) == 2:
        p_start, p_end = pd.Timestamp(c[0]), pd.Timestamp(c[1]) + pd.Timedelta(days=1)
    else:
        p_start, p_end = month_start, month_start + pd.DateOffset(months=1)
else:
    p_start, p_end = PRESETS[choice]
p_start, p_end = pd.Timestamp(p_start).normalize(), pd.Timestamp(p_end).normalize()
sb.caption(f"Window: {p_start:%d %b %Y} → {(p_end - pd.Timedelta(days=1)):%d %b %Y}. Occupancy counts any stay overlapping it.")

dim = df[df["property"].isin(sel_props) & df["platform"].isin(sel_plats)].copy()
mask = pd.Series(False, index=dim.index)
if "Booked" in sel_status:
    mask |= ~dim["is_cancelled"]
if "Cancelled" in sel_status:
    mask |= dim["is_cancelled"]
fdf = dim[mask].copy()

units = max(len(sel_props), 1)
ps = m.period_summary(fdf, p_start, p_end, units)

st.markdown('<div class="hdr-bar"><div class="hdr-left"><div class="eyebrow">Portfolio</div><div class="pg-title">Short-term rental performance</div></div><div class="hdr-btns"><span class="pg-btn">Export</span></div></div>', unsafe_allow_html=True)
CONTEXT_LINE = (f'<div class="pg-context">Confirmed bookings · {dq.rows_loaded} stays · {choice} · as at {TODAY:%d %b %Y}</div>')

tabs = st.tabs(["Calendar", "Overview", "Revenue & pace", "Operations", "Properties", "Cancellations"])

with tabs[0]:
    st.markdown(CONTEXT_LINE, unsafe_allow_html=True)
    calendar_view.render(df, TODAY, p_start)

with tabs[1]:
    cards([
        ("Net payout (period)", money(ps["net_revenue"]), "nights stayed in window"),
        ("Gross guest total", money(ps["gross_revenue"]), "before fees"),
        ("Occupancy", pct(ps["occupancy"]), f'{num(ps["occupied_nights"])}/{num(ps["available_nights"])} nights'),
        ("RevPAR", money(ps["revpar"]), f"{units} unit(s)"),
    ])
    st.write("")
    cards([
        ("ADR (net)", money(ps["adr_net"]), "net / occupied night"),
        ("ADR (gross)", money(ps["adr_gross"]), "gross / occupied night"),
        ("Stays in period", num(ps["bookings"]), f'avg {ps["avg_los"]:.1f} nts'),
        ("Avg lead time", f'{ps["avg_lead_time"]:.0f} d', "book → check-in"),
    ])
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-h">Net payout by property</div>', unsafe_allow_html=True)
        pr = m.period_by_dimension(fdf, p_start, p_end, "property")
        if not pr.empty:
            st.altair_chart(bar(pr, "property", "net_revenue", "property"), use_container_width=True)
    with c2:
        st.markdown('<div class="section-h">Net payout by platform</div>', unsafe_allow_html=True)
        pl = m.period_by_dimension(fdf, p_start, p_end, "platform")
        if not pl.empty:
            st.altair_chart(bar(pl, "platform", "net_revenue", "platform"), use_container_width=True)
    st.markdown('<div class="section-h">Portfolio by stay timing (all dates)</div>', unsafe_allow_html=True)
    timing = (m.active(fdf).groupby("stay_state")["revenue_net"].sum().reindex(["Historical", "Current", "Future"]).fillna(0).reset_index())
    st.altair_chart(bar(timing, "stay_state", "revenue_net", "stay_state", scheme=["#b9c0c7", "#c98a3a", "#2f6f6a"]), use_container_width=True)

with tabs[2]:
    st.caption("Forward view — independent of the reporting period above.")
    st.markdown('<div class="section-h">Booking pace — net payout by check-in month</div>', unsafe_allow_html=True)
    pace = m.pace_by_checkin_month(fdf, TODAY)
    if not pace.empty:
        chart = alt.Chart(pace).mark_bar(size=34, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("month:N", sort=list(pace["month"]), title=None, axis=alt.Axis(labelAngle=-40)),
            y=alt.Y("revenue_net:Q", title="Net payout", axis=alt.Axis(format="$,.0f")),
            color=alt.Color("period:N", scale=alt.Scale(domain=["Past", "Future"], range=["#b9c0c7", "#2f6f6a"]), legend=alt.Legend(title=None, orient="top")),
            tooltip=["month", alt.Tooltip("revenue_net:Q", format="$,.0f"), "period"],
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    st.markdown('<div class="section-h">Monthly occupancy — next 12 months</div>', unsafe_allow_html=True)
    mo = m.monthly_series(fdf, units, month_start, month_start + pd.DateOffset(months=12))
    if not mo.empty:
        st.altair_chart(month_bar(mo, "occupancy", "Occupancy", ".0%"), use_container_width=True)

with tabs[3]:
    st.caption(f"Activity within {p_start:%d %b} → {(p_end - pd.Timedelta(days=1)):%d %b %Y}.")
    a = m.allocate(fdf, p_start, p_end)
    arr = m.active(fdf)
    arrivals = int(((arr["check_in"] >= p_start) & (arr["check_in"] < p_end)).sum())
    departures = int(((arr["check_out"] >= p_start) & (arr["check_out"] < p_end)).sum())
    cards([("Stays in period", num(len(a)), "overlapping the window"), ("Arrivals in period", num(arrivals), ""), ("Departures in period", num(departures), "")])
    st.write("")
    st.markdown('<div class="section-h">Stays overlapping the period</div>', unsafe_allow_html=True)
    if not a.empty:
        view = a.sort_values("check_in")[["property", "platform", "guest", "check_in", "check_out", "los", "nights_in", "revenue_net", "stay_state"]].copy()
        for dcol in ("check_in", "check_out"):
            view[dcol] = view[dcol].apply(day)
        view["revenue_net"] = view["revenue_net"].apply(money)
        view = view.rename(columns={"property":"Property","platform":"Platform","guest":"Guest","check_in":"Check-in","check_out":"Check-out","los":"Nights","nights_in":"Nights in period","revenue_net":"Net payout","stay_state":"Timing"})
        st.dataframe(view, use_container_width=True, hide_index=True)
    else:
        st.info("No stays overlap this period.")

with tabs[4]:
    st.caption(f"Per-property performance for {choice.lower()}.")
    rows = []
    for p in sel_props:
        sub = fdf[fdf["property"] == p]
        s = m.period_summary(sub, p_start, p_end, 1)
        rows.append({"Property": p, "Occupancy": pct(s["occupancy"]), "Net payout": money(s["net_revenue"]), "Nights": num(s["occupied_nights"]), "ADR (net)": money(s["adr_net"]), "RevPAR": money(s["revpar"]), "Stays": num(s["bookings"])})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        pr = m.period_by_dimension(fdf, p_start, p_end, "property")
        if not pr.empty:
            st.altair_chart(bar(pr, "property", "net_revenue", "property", y_title="Net payout (period)"), use_container_width=True)

with tabs[5]:
    st.caption("All cancellations for the selected properties/platforms (all dates).")
    cstats = m.cancellation_stats(dim)
    cards([("Cancellation rate", pct(cstats["rate"]), f'{cstats["cancelled"]} of {cstats["total"]}'), ("Cancelled bookings", num(cstats["cancelled"]), ""), ("Lost net payout", money(cstats["lost_net"]), "value of cancellations")])
    st.write("")
    if cstats["by_platform"]:
        bp = pd.DataFrame([{"platform": k2, "cancelled": v} for k2, v in cstats["by_platform"].items()])
        st.markdown('<div class="section-h">Cancellations by platform</div>', unsafe_allow_html=True)
        st.altair_chart(bar(bp, "platform", "cancelled", "platform", y_title="Cancelled", fmt="d"), use_container_width=True)

with st.expander("Data quality & assumptions"):
    st.markdown(f"""
- **Rows loaded:** {dq.rows_loaded} · **usable:** {dq.rows_usable} · **cancelled:** {dq.cancelled_rows} · **manual overrides used:** {dq.manual_overrides_used}
- **Occupancy model:** nights occupied within the reporting window ÷ nights available ({units} unit(s) × window nights). **Any stay overlapping the window counts** — check-in date is not used to include/exclude. Revenue is allocated night-by-night.
- **Cancelled and invalid-date rows are excluded** from occupancy/revenue everywhere (shown only on the Cancellations tab), per the reporting rules.
- **Occupancy assumes {units} always-available unit(s)** — owner-blocked/maintenance nights are not modelled.
- **Net payout** parsed from text (`$1,430` → number); **Guest total** kept as gross. **Booking.com** rows carry no fee breakdown or guest headcount.
""")
    for msg in dq.messages:
        st.caption("• " + msg)
