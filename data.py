"""Read-only loader for the STR 'Confirmed Bookings' tab.

Reuses the existing Booking.com-sync OAuth credentials (../token.json) — no new
auth system. Does not write to the sheet. All parsing is defensive: bad values
become NaN/NaT and are recorded in `notes` rather than raising.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = REPO_ROOT / "token.json"
ENV_FILE = REPO_ROOT / ".env"
SHEET_TAB = "Confirmed Bookings"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

COLUMN_MAP = {
    "booking id": "booking_id", "booked on": "booked_on", "platform": "platform",
    "status": "status", "property": "property_raw", "guests": "guests",
    "guest": "guest", "check-in": "check_in", "check-out": "check_out",
    "cancelled on": "cancelled_on", "nights": "nights", "lead time": "lead_time_days",
    "net payout (manual)": "net_payout_manual", "net payout": "net_payout",
    "guest total": "guest_total",
}

PROPERTY_SHORT = {"darlinghurst": "Darlinghurst", "surry hills": "Surry Hills"}

@dataclass
class DataQuality:
    rows_loaded: int = 0
    rows_usable: int = 0
    dropped_missing_dates: int = 0
    dropped_missing_revenue: int = 0
    cancelled_rows: int = 0
    guests_blank: int = 0
    manual_overrides_used: int = 0
    unmapped_properties: list = field(default_factory=list)
    messages: list = field(default_factory=list)

def _secrets():
    try:
        import streamlit as st
        return st.secrets
    except Exception:
        return None

def _read_sheet_id() -> str:
    sec = _secrets()
    if sec is not None:
        try:
            if "GOOGLE_SHEET_ID" in sec:
                return str(sec["GOOGLE_SHEET_ID"])
        except Exception:
            pass
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("GOOGLE_SHEET_ID="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("GOOGLE_SHEET_ID not set (Streamlit secrets) or in ../.env")

def _credentials():
    sec = _secrets()
    if sec is not None:
        try:
            if "gcp_service_account" in sec:
                from google.oauth2.service_account import Credentials as SA
                return SA.from_service_account_info(dict(sec["gcp_service_account"]), scopes=SCOPES)
        except Exception:
            pass
        try:
            if "google_token" in sec:
                return Credentials.from_authorized_user_info(dict(sec["google_token"]), SCOPES)
        except Exception:
            pass
    if TOKEN_FILE.exists():
        return Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    raise RuntimeError("No Google credentials. Set st.secrets ('gcp_service_account' or 'google_token') for cloud, or create token.json locally.")

def _fetch_rows() -> list[list[str]]:
    service = build("sheets", "v4", credentials=_credentials(), cache_discovery=False)
    resp = service.spreadsheets().values().get(
        spreadsheetId=_read_sheet_id(), range=f"'{SHEET_TAB}'!A1:AZ2000"
    ).execute()
    return resp.get("values", [])

def _money(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(r"[^0-9.\-]", "", regex=True).replace("", pd.NA)
    return pd.to_numeric(cleaned, errors="coerce")

def _resolve_columns(header: list[str]) -> dict[str, int]:
    norm = [re.sub(r"\s+", " ", (h or "")).strip().lower() for h in header]
    resolved: dict[str, int] = {}
    for needle, canon in sorted(COLUMN_MAP.items(), key=lambda kv: -len(kv[0])):
        for i, h in enumerate(norm):
            if needle in h and canon not in resolved and i not in resolved.values():
                resolved[canon] = i
                break
    return resolved

def load_bookings() -> tuple[pd.DataFrame, DataQuality]:
    rows = _fetch_rows()
    dq = DataQuality()
    if not rows:
        dq.messages.append("Sheet returned no rows.")
        return pd.DataFrame(), dq
    header, *body = rows
    cols = _resolve_columns(header)
    body = [r for r in body if any(c.strip() for c in r)]
    dq.rows_loaded = len(body)
    width = len(header)
    padded = [r + [""] * (width - len(r)) for r in body]
    raw = pd.DataFrame(padded, columns=range(width))
    df = pd.DataFrame()
    for canon, idx in cols.items():
        df[canon] = raw[idx]
    for date_col in ("booked_on", "check_in", "check_out", "cancelled_on"):
        if date_col in df:
            df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
    for num_col in ("guests", "nights", "lead_time_days"):
        if num_col in df:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
    for money_col in ("net_payout", "guest_total", "net_payout_manual"):
        if money_col in df:
            df[money_col] = _money(df[money_col])
    df["property"] = df.get("property_raw", "").astype(str).apply(_short_property)
    dq.unmapped_properties = sorted({p for p, s in zip(df.get("property_raw", []), df["property"]) if s == p and p})
    status = df.get("status", pd.Series("", index=df.index)).astype(str).str.strip()
    df["is_cancelled"] = status.str.lower().eq("cancelled") | df.get("cancelled_on", pd.Series(pd.NaT, index=df.index)).notna()
    dq.cancelled_rows = int(df["is_cancelled"].sum())
    manual = df.get("net_payout_manual", pd.Series(pd.NA, index=df.index))
    df["revenue_net"] = df.get("net_payout").where(manual.isna(), manual)
    dq.manual_overrides_used = int(manual.notna().sum())
    df["revenue_gross"] = df.get("guest_total")
    derived_los = (df["check_out"] - df["check_in"]).dt.days
    df["los"] = df.get("nights").fillna(derived_los)
    derived_lead = (df["check_in"] - df["booked_on"]).dt.days
    df["lead_time_days"] = df.get("lead_time_days").fillna(derived_lead)
    if "guests" in df:
        dq.guests_blank = int(df["guests"].isna().sum())
    bad_dates = df["check_in"].isna() | df["check_out"].isna() | (df["check_out"] <= df["check_in"])
    bad_rev = df["revenue_net"].isna()
    dq.dropped_missing_dates = int(bad_dates.sum())
    dq.dropped_missing_revenue = int((~bad_dates & bad_rev).sum())
    df["usable"] = ~bad_dates
    dq.rows_usable = int(df["usable"].sum())
    today = pd.Timestamp.today().normalize()
    df["stay_state"] = "Future"
    df.loc[df["check_out"] <= today, "stay_state"] = "Historical"
    df.loc[(df["check_in"] <= today) & (df["check_out"] > today), "stay_state"] = "Current"
    if dq.guests_blank:
        dq.messages.append(f"{dq.guests_blank} rows have no guest headcount (Booking.com does not supply it) — per-guest metrics would be Airbnb-only.")
    if dq.dropped_missing_dates:
        dq.messages.append(f"{dq.dropped_missing_dates} rows dropped from occupancy/ADR: missing or invalid check-in/check-out dates.")
    return df.reset_index(drop=True), dq

def _short_property(name: str) -> str:
    low = name.lower()
    for key, short in PROPERTY_SHORT.items():
        if key in low:
            return short
    return name.strip()
