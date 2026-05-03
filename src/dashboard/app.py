import os
from datetime import date, datetime, timezone

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="BrandIQ", page_icon="🎯")

st.markdown("""
<style>
#MainMenu{visibility:hidden;}
footer{visibility:hidden;}
header{visibility:hidden;}
.block-container{padding:0!important;margin:0!important;max-width:100%!important;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Live data from Railway DB (graceful fallback to zeros if unavailable)
# ---------------------------------------------------------------------------

def _today() -> str:
    d = date.today()
    return f"{d} 00:00:00+00"


def _fetch_kpis() -> dict:
    db_url = os.getenv("DATABASE_URL_SYNC", "")
    if not db_url or "REPLACE_ME" in db_url:
        return {"posts": 0, "leads": 0, "hot_leads": 0, "wa_sent": 0, "trials": 0}
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        today = _today()
        with engine.connect() as conn:
            def q(sql): return conn.execute(text(sql), {"t": today}).scalar() or 0
            return {
                "posts":     q("SELECT COUNT(*) FROM posts WHERE posted_at >= :t AND status='posted'"),
                "leads":     q("SELECT COUNT(*) FROM leads WHERE created_at >= :t"),
                "hot_leads": q("SELECT COUNT(*) FROM leads WHERE status='hot' AND created_at >= :t"),
                "wa_sent":   q("SELECT COUNT(*) FROM whatsapp_sequences WHERE sent_at >= :t AND status='sent'"),
                "trials":    q("SELECT COUNT(*) FROM adaptiq_trials WHERE trial_start >= :t"),
            }
    except Exception as e:
        st.warning(f"DB unavailable: {e}")
        return {"posts": 0, "leads": 0, "hot_leads": 0, "wa_sent": 0, "trials": 0}


kpis = _fetch_kpis()

# ---------------------------------------------------------------------------
# Load HTML and inject live KPI values
# ---------------------------------------------------------------------------

html_path = os.path.join(os.path.dirname(__file__), "brandiq_ui.html")
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# Replace mock KPI values with live data using placeholder markers
replacements = {
    'kpi-1"><div class="kpi-lbl">Posts Today</div><div class="kpi-val" style="color:var(--accent)">5':
        f'kpi-1"><div class="kpi-lbl">Posts Today</div><div class="kpi-val" style="color:var(--accent)">{kpis["posts"]}',
    'kpi-2"><div class="kpi-lbl">New Leads</div><div class="kpi-val" style="color:var(--accent4)">34':
        f'kpi-2"><div class="kpi-lbl">New Leads</div><div class="kpi-val" style="color:var(--accent4)">{kpis["leads"]}',
    'kpi-4"><div class="kpi-lbl">Adaptiq Trials</div><div class="kpi-val" style="color:var(--purple)">142':
        f'kpi-4"><div class="kpi-lbl">Adaptiq Trials</div><div class="kpi-val" style="color:var(--purple)">{kpis["trials"]}',
}
for old, new in replacements.items():
    html = html.replace(old, new)

components.html(html, height=900, scrolling=True)
