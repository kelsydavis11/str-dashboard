"""Visual system — refined operational SaaS dashboard.

Inter throughout, cool neutral field with clearly defined white surfaces,
restrained sage/terracotta accents used semantically (property identity,
attention). Hierarchy via size/weight/colour, not decoration. One THEME dict
drives both this CSS and the HTML builders in calendar_view.
"""
from __future__ import annotations

import altair as alt

THEME = {
    "bg_page": "#F5F6F8",
    "bg_sunken": "#EEF0F3",
    "card_bg": "#FFFFFF",
    "rule": "#E3E5E9",
    "rule_soft": "#ECEEF1",
    "rule_strong": "#CDD1D7",
    "ink": "#1C1E23",
    "ink_mid": "#565B63",
    "ink_soft": "#787E88",
    "terracotta": "#8F5340",
    "sage": "#5C6E54",
    "sage_deep": "#52604D",
    "sage_tint": "#E9EEE6",
    "terra_tint": "#F6EDE9",
    "pos": "#3F7A43",
    "neg": "#A8534A",
    "warn": "#A67C2E",
    "props": {
        "Excelsior Surry Hills Retreat":
            {"base": "#52604D", "chip": "rgba(82,96,77,.10)", "short": "Surry Hills"},
        "Modern Darlinghurst Apartment":
            {"base": "#8F5340", "chip": "rgba(143,83,64,.10)", "short": "Darlinghurst"},
    },
    "extra": ["#4C5B8C", "#6E5A3E"],
}

INK = THEME["ink"]
MUTED = THEME["ink_soft"]
ACCENT = THEME["sage_deep"]
PLATFORM_COLORS = {"Airbnb": "#8F5340", "Booking.com": "#52604D"}
PROPERTY_COLORS = {"Surry Hills": "#52604D", "Darlinghurst": "#8F5340"}

FONT = "'Inter', -apple-system, 'Segoe UI', Roboto, system-ui, sans-serif"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root {
  --bg-page:#F5F6F8; --bg-sunken:#EEF0F3; --surface:#FFFFFF; --card-bg:#FFFFFF;
  --rule:#E3E5E9; --rule-soft:#ECEEF1; --rule-strong:#CDD1D7;
  --ink:#1C1E23; --ink-mid:#565B63; --ink-soft:#787E88;
  --terracotta:#8F5340; --sage:#5C6E54; --sage-deep:#52604D; --sage-tint:#E9EEE6; --terra-tint:#F6EDE9;
  --pos:#3F7A43; --neg:#A8534A; --warn:#A67C2E;
  --font:'Inter',-apple-system,'Segoe UI',Roboto,system-ui,sans-serif;
}
.stApp { background:var(--bg-page); }
header[data-testid="stHeader"] { background:transparent; height:0; }
#MainMenu, footer, [data-testid="stToolbar"] { display:none; }
.block-container { padding:1.6rem 2.2rem 2.4rem; max-width:1500px; }
html, body, [class*="css"], .stMarkdown, p, span, div, label, input, button, .stTabs { font-family:var(--font); color:var(--ink); }
[data-testid="stVerticalBlock"] { gap:0.55rem; }
.num { font-variant-numeric:tabular-nums; }
.hdr-bar { display:flex; align-items:flex-start; justify-content:space-between; padding:0 2px; margin-bottom:4px; }
.hdr-left { display:flex; flex-direction:column; gap:3px; }
.eyebrow { font-size:12px; font-weight:500; color:var(--ink-soft); }
.pg-title { font-size:22px; font-weight:600; letter-spacing:-.01em; color:var(--ink); line-height:1.2; }
.pg-btn { height:34px; box-sizing:border-box; display:inline-flex; align-items:center; font-size:13px; font-weight:500; padding:0 15px; border-radius:6px; border:1px solid var(--rule-strong); background:var(--surface); color:var(--ink); text-decoration:none; }
.pg-btn:hover { background:var(--bg-sunken); }
.pg-context { color:var(--ink-soft); font-size:13px; padding:2px 2px 0; }
.stTabs [data-baseweb="tab-list"] { gap:28px; border-bottom:1px solid var(--rule); margin:8px 0 2px; }
.stTabs [data-baseweb="tab"] { background:transparent; padding:4px 0 12px; font-size:13px; font-weight:500; color:var(--ink-soft); }
.stTabs [data-baseweb="tab"]:hover { color:var(--ink-mid); }
.stTabs [aria-selected="true"] { color:var(--ink); box-shadow:inset 0 -2px 0 var(--sage-deep); }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }
.stTabs [data-baseweb="tab-panel"] { padding-top:.8rem; }
.kpi { background:var(--surface); border:1px solid var(--rule); border-radius:8px; padding:16px 18px; height:100%; }
.kpi .lbl { font-size:12px; font-weight:500; color:var(--ink-soft); margin-bottom:.45rem; }
.kpi .val { font-size:26px; font-weight:600; letter-spacing:-.01em; line-height:1.05; font-variant-numeric:tabular-nums; }
.kpi .sub { font-size:12px; color:var(--ink-soft); margin-top:.35rem; }
.section-h { font-size:14px; font-weight:600; margin:.5rem 0 .4rem; color:var(--ink); }
[data-testid="stDataFrame"] { border:1px solid var(--rule); border-radius:8px; }
.stApp [data-testid="stExpander"] { border:1px solid var(--rule); border-radius:8px; background:var(--surface); }
.stButton > button, [data-testid="stBaseButton-secondary"] { border-radius:6px !important; border:1px solid var(--rule-strong) !important; background:var(--surface) !important; color:var(--ink) !important; font-size:13px !important; font-weight:500 !important; }
.stButton > button:hover { background:var(--bg-sunken) !important; }
section[data-testid="stSidebar"] { background:var(--bg-sunken); border-right:1px solid var(--rule); }
section[data-testid="stSidebar"] label { font-size:12px; font-weight:500; color:var(--ink-soft); }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small { font-size:12px; color:var(--ink-soft); line-height:1.55; }
[data-baseweb="tag"] { background:var(--sage-tint) !important; border:1px solid var(--rule) !important; border-radius:4px !important; }
[data-baseweb="tag"] span, [data-baseweb="tag"] div { color:var(--sage-deep) !important; }
[data-baseweb="tag"] svg { fill:var(--sage-deep) !important; }
</style>
"""


def kpi_card(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    return (f'<div class="kpi"><div class="lbl">{label}</div>'
            f'<div class="val">{value}</div>{sub_html}</div>')


def altair_theme():
    return {
        "config": {
            "font": FONT,
            "view": {"stroke": "transparent"},
            "axis": {"labelColor": MUTED, "titleColor": MUTED, "titleFontWeight": 500,
                     "grid": True, "gridColor": "#ECEEF1", "domain": False,
                     "tickColor": "#ECEEF1", "labelFontSize": 11, "titleFontSize": 11},
            "legend": {"labelColor": INK, "titleColor": MUTED, "titleFontSize": 11},
            "range": {"category": ["#52604D", "#8F5340", "#4C5B8C", "#6E5A3E"]},
        }
    }


def register_theme():
    alt.themes.register("str_dash", altair_theme)
    alt.themes.enable("str_dash")
