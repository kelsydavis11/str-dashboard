"""Metric computations for the STR dashboard.

Core model: a **reporting period** [start, end) is a real calendar window. Any
active stay that OVERLAPS the window contributes the nights that fall inside it
(check-in date is irrelevant to whether it counts). Revenue is allocated
night-by-night, so a stay spanning the window edge is split correctly.

Revenue prefers Net payout (`revenue_net`); gross Guest total (`revenue_gross`)
is kept separately. Cancelled/unusable rows are excluded everywhere except the
cancellation report.
"""
from __future__ import annotations

import pandas as pd


def active(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df[df["usable"] & ~df["is_cancelled"]].copy()


def overlapping(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    a = active(df)
    if a.empty:
        return a
    return a[(a["check_in"] < end) & (a["check_out"] > start)].copy()


def allocate(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    a = overlapping(df, start, end)
    if a.empty:
        return a
    lo = a["check_in"].clip(lower=start)
    hi = a["check_out"].clip(upper=end)
    a["nights_in"] = (hi - lo).dt.days.clip(lower=0)
    frac = (a["nights_in"] / a["los"]).where(a["los"] > 0, 0.0)
    a["net_in"] = a["revenue_net"] * frac
    a["gross_in"] = a["revenue_gross"] * frac
    return a


def period_summary(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, units: int) -> dict:
    a = allocate(df, start, end)
    window_nights = max((end - start).days, 0)
    available = units * window_nights
    occupied = float(a["nights_in"].sum()) if not a.empty else 0.0
    net = float(a["net_in"].sum()) if not a.empty else 0.0
    gross = float(a["gross_in"].sum()) if not a.empty else 0.0
    return {
        "bookings": int(len(a)),
        "occupied_nights": occupied,
        "available_nights": float(available),
        "occupancy": occupied / available if available else 0.0,
        "net_revenue": net,
        "gross_revenue": gross,
        "adr_net": net / occupied if occupied else 0.0,
        "adr_gross": gross / occupied if occupied else 0.0,
        "revpar": net / available if available else 0.0,
        "avg_los": float(a["los"].mean()) if not a.empty else 0.0,
        "avg_lead_time": float(a["lead_time_days"].dropna().mean()) if not a.empty else 0.0,
    }


def period_by_dimension(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, dim: str) -> pd.DataFrame:
    a = allocate(df, start, end)
    if a.empty:
        return pd.DataFrame()
    g = a.groupby(dim).agg(
        bookings=(dim, "count"),
        net_revenue=("net_in", "sum"),
        gross_revenue=("gross_in", "sum"),
        nights=("nights_in", "sum"),
    ).reset_index()
    g["adr_net"] = (g["net_revenue"] / g["nights"]).where(g["nights"] > 0, 0.0)
    return g.sort_values("net_revenue", ascending=False)


def monthly_series(df: pd.DataFrame, units: int, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    months = pd.period_range(start, end - pd.Timedelta(days=1), freq="M")
    out = []
    for month in months:
        s = month.to_timestamp()
        e = (month + 1).to_timestamp()
        ps = period_summary(df, s, e, units)
        out.append({
            "month": month.strftime("%b %Y"),
            "occupancy": ps["occupancy"],
            "revpar": ps["revpar"],
            "net_revenue": ps["net_revenue"],
            "occupied_nights": ps["occupied_nights"],
        })
    return pd.DataFrame(out)


def pace_by_checkin_month(df: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    a = active(df).dropna(subset=["check_in"])
    if a.empty:
        return pd.DataFrame(columns=["month", "revenue_net", "period"])
    g = a.assign(month=a["check_in"].dt.to_period("M"))
    agg = g.groupby("month", as_index=False)["revenue_net"].sum()
    cutoff = today.to_period("M").to_timestamp()
    agg["period"] = agg["month"].apply(lambda m: "Future" if m.to_timestamp() >= cutoff else "Past")
    agg["month"] = agg["month"].dt.strftime("%b %Y")
    return agg


def cancellation_stats(df: pd.DataFrame) -> dict:
    total = len(df)
    cancelled = df[df["is_cancelled"]]
    return {
        "total": int(total),
        "cancelled": int(len(cancelled)),
        "rate": float(len(cancelled) / total) if total else 0.0,
        "lost_net": float(cancelled["revenue_net"].sum()),
        "by_platform": cancelled.groupby("platform").size().to_dict() if len(cancelled) else {},
    }
