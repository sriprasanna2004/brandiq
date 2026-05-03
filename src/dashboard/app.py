import os
import time
from datetime import datetime

import httpx
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="BrandIQ", page_icon="🎯")

API = os.getenv("API_URL", "http://api:8000")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500&display=swap');
*, body { font-family: 'DM Sans', sans-serif; }
.stApp { background: #07080f; color: #e8eaf6; }
section[data-testid="stSidebar"] { background: #0d0f1a; border-right: 1px solid #1c1f32; }
section[data-testid="stSidebar"] * { color: #e8eaf6 !important; }
.block-container { padding: 1.5rem 2rem !important; max-width: 100% !important; }
div[data-testid="metric-container"] {
    background: #0d0f1a; border: 1px solid #1c1f32; border-radius: 10px;
    padding: 14px 16px;
}
div[data-testid="metric-container"] label { color: #4a4f72 !important; font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 800; }
.stButton > button {
    background: #00e5c3; color: #000; font-weight: 700; border: none;
    border-radius: 6px; padding: 6px 16px; font-size: 12px;
}
.stButton > button:hover { background: #00c9aa; }
div[data-testid="stDataFrame"] { border: 1px solid #1c1f32; border-radius: 8px; }
h1, h2, h3 { font-family: 'Syne', sans-serif; color: #e8eaf6; }
.stSelectbox label, .stTextInput label { color: #4a4f72 !important; font-size: 11px; }
hr { border-color: #1c1f32; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def api_get(path: str) -> dict | list | None:
    try:
        r = httpx.get(f"{API}{path}", timeout=5)
        return r.json() if r.is_success else None
    except Exception:
        return None


def api_post(path: str, body: dict = {}) -> dict | None:
    try:
        r = httpx.post(f"{API}{path}", json=body, timeout=10)
        return r.json() if r.is_success else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🎯 BrandIQ")
    st.caption("TOPPER IAS · ADAPTIQ")
    st.divider()

    page = st.radio(
        "Navigate",
        ["Overview", "Content Queue", "Leads", "Agent Jobs", "Analytics", "Settings"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Quick Actions**")

    if st.button("▶ Run Content Crew", use_container_width=True):
        res = api_post("/tasks/content")
        if res and "task_id" in res:
            st.success(f"Queued: {res['task_id'][:8]}...")
        else:
            st.error(str(res))

    if st.button("▶ Run Analytics", use_container_width=True):
        res = api_post("/tasks/analytics")
        if res and "task_id" in res:
            st.success(f"Queued: {res['task_id'][:8]}...")
        else:
            st.error(str(res))

    st.divider()

    # System status
    st.markdown("**System Status**")
    health = api_get("/health")
    st.markdown(f"{'🟢' if health else '🔴'} API {'Online' if health else 'Offline'}")
    st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')}")

    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ---------------------------------------------------------------------------
# KPI row (shown on all pages)
# ---------------------------------------------------------------------------

kpis = api_get("/stats/kpis") or {}

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📸 Posts Today",    kpis.get("posts_today", 0))
c2.metric("👤 New Leads",      kpis.get("new_leads", 0))
c3.metric("🔥 Hot Leads",      kpis.get("hot_leads", 0))
c4.metric("💬 WhatsApp Sent",  kpis.get("wa_sent", 0))
c5.metric("📱 Adaptiq Trials", kpis.get("trials_today", 0))

st.divider()


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

if page == "Overview":
    st.markdown("### 🏠 Overview")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Total Posts Published**")
        st.metric("All Time", kpis.get("total_posts", 0))
        st.markdown("**Total Leads Captured**")
        st.metric("All Time", kpis.get("total_leads", 0))

    with col_b:
        st.markdown("**Recent Agent Jobs**")
        jobs = api_get("/stats/agent-jobs") or []
        if jobs:
            import pandas as pd
            df = pd.DataFrame(jobs)[["agent_name", "status", "created_at"]]
            df.columns = ["Agent", "Status", "Started"]
            st.dataframe(df.head(8), use_container_width=True, hide_index=True)
        else:
            st.info("No agent jobs yet.")

    st.markdown("**Trigger a Lead Nurture Manually**")
    with st.form("manual_lead"):
        ig = st.text_input("Instagram Handle")
        msg = st.text_input("Message Text")
        day = st.selectbox("Day Number", [0, 1, 3, 7, 14])
        if st.form_submit_button("Send"):
            res = api_post("/tasks/lead", {"ig_handle": ig, "message_text": msg, "day_number": day})
            st.success(str(res)) if res and "task_id" in res else st.error(str(res))


elif page == "Content Queue":
    st.markdown("### 📅 Content Queue")

    status_filter = st.selectbox("Filter by status", ["all", "pending", "approved", "posted", "failed"])
    posts = api_get(f"/posts?status={status_filter}&limit=30") if status_filter != "all" else api_get("/posts?limit=30")
    posts = posts or []

    if not posts:
        st.info("No posts found.")
    else:
        for p in posts:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                col1.write(f"**{p['caption_a'][:60]}...**")
                col2.write(p["platform"])

                status_colors = {"pending": "🟡", "approved": "🔵", "posted": "🟢", "failed": "🔴"}
                col3.write(f"{status_colors.get(p['status'], '⚪')} {p['status']}")
                col4.write((p.get("scheduled_at") or "")[:16])

                if p["status"] == "pending":
                    if col5.button("✅ Approve", key=f"approve_{p['id']}"):
                        res = api_post("/posts/approve", {"post_id": p["id"]})
                        st.success("Approved") if res and res.get("status") == "approved" else st.error(str(res))
                        st.cache_data.clear()
                        st.rerun()
                elif p["status"] == "approved":
                    if col5.button("🚀 Publish", key=f"publish_{p['id']}"):
                        res = api_post(f"/posts/publish/{p['id']}")
                        st.success("Published!") if res and res.get("published") else st.error(str(res))
                        st.cache_data.clear()
                        st.rerun()
                else:
                    col5.write("")
                st.divider()


elif page == "Leads":
    st.markdown("### 👥 Leads")

    col_filter, col_search = st.columns([2, 3])
    status_f = col_filter.selectbox("Status", ["all", "hot", "warm", "cold", "opted_out"])
    leads = api_get(f"/leads?status={status_f}&limit=50") if status_f != "all" else api_get("/leads?limit=50")
    leads = leads or []

    if not leads:
        st.info("No leads yet.")
    else:
        import pandas as pd
        df = pd.DataFrame(leads)[["ig_handle", "name", "phone", "status", "source", "created_at"]]
        df.columns = ["Handle", "Name", "Phone", "Status", "Source", "Created"]

        def color_status(val):
            c = {"hot": "background-color:#ff6b6b30", "warm": "background-color:#ffd16630",
                 "cold": "background-color:#4facfe30", "opted_out": "background-color:#ffffff15"}
            return c.get(val, "")

        st.dataframe(
            df.style.applymap(color_status, subset=["Status"]),
            use_container_width=True, hide_index=True,
        )

        st.markdown("**Send Nurture Message to a Lead**")
        with st.form("nurture_form"):
            handles = [l["ig_handle"] for l in leads]
            selected = st.selectbox("Select Lead", handles)
            day_n = st.selectbox("Nurture Day", [1, 3, 7, 14])
            if st.form_submit_button("Send WhatsApp Nurture"):
                res = api_post("/tasks/lead", {"ig_handle": selected, "message_text": "", "day_number": day_n})
                st.success(f"Queued: {res}") if res else st.error("Failed")


elif page == "Agent Jobs":
    st.markdown("### 🤖 Agent Job Log")

    jobs = api_get("/stats/agent-jobs") or []
    if not jobs:
        st.info("No jobs yet.")
    else:
        import pandas as pd
        df = pd.DataFrame(jobs)
        df = df[["agent_name", "status", "job_id", "created_at", "completed_at", "error"]]
        df.columns = ["Agent", "Status", "Job ID", "Started", "Completed", "Error"]

        def color_job(val):
            c = {"success": "background-color:#00e5c330", "failed": "background-color:#ff6b6b30",
                 "running": "background-color:#ffd16630", "pending": "background-color:#4facfe20"}
            return c.get(val, "")

        st.dataframe(
            df.style.applymap(color_job, subset=["Status"]),
            use_container_width=True, hide_index=True,
        )


elif page == "Analytics":
    st.markdown("### 📊 Analytics")

    import json
    redis_url = os.getenv("REDIS_URL", "")
    summary = None
    if redis_url:
        try:
            import redis as redis_lib
            r = redis_lib.from_url(redis_url, decode_responses=True, socket_connect_timeout=3)
            raw = r.get("analytics:weekly_summary")
            if raw:
                summary = json.loads(raw)
        except Exception:
            pass

    if summary:
        col1, col2 = st.columns(2)
        col1.metric("Weekly Reach", summary.get("weekly_reach_total", 0))
        col2.metric("Leads Generated", summary.get("weekly_leads_generated", 0))

        st.markdown("**Insight**")
        st.info(summary.get("insight_text", ""))

        st.markdown("**Recommended Content Mix**")
        mix = summary.get("recommended_content_mix", {})
        if mix:
            import pandas as pd
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(
                x=list(mix.keys()), y=list(mix.values()),
                marker_color=["#00e5c3", "#4facfe", "#ffd166", "#ff6b6b", "#9d6fff"],
            ))
            fig.update_layout(
                paper_bgcolor="#07080f", plot_bgcolor="#0d0f1a",
                font_color="#e8eaf6", height=280,
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Top Performers**")
        st.json(summary.get("top_performers", []))
    else:
        st.info("No analytics data yet — runs tonight at 11 PM, or trigger it manually from the sidebar.")

    if st.button("▶ Run Analytics Now"):
        res = api_post("/tasks/analytics")
        st.success(f"Queued: {res}")


elif page == "Settings":
    st.markdown("### ⚙️ Settings")

    st.markdown("**Environment**")
    env_vars = {
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "—"),
        "ANTHROPIC_API_KEY": "sk-ant-***" if os.getenv("ANTHROPIC_API_KEY") else "NOT SET",
        "META_ACCESS_TOKEN": "EAAj***" if os.getenv("META_ACCESS_TOKEN") else "NOT SET",
        "TELEGRAM_BOT_TOKEN": "***" if os.getenv("TELEGRAM_BOT_TOKEN") else "NOT SET",
        "WHATSAPP_PHONE_NUMBER_ID": os.getenv("WHATSAPP_PHONE_NUMBER_ID", "NOT SET"),
        "STABILITY_API_KEY": "***" if os.getenv("STABILITY_API_KEY") else "NOT SET",
        "SENTRY_DSN": "configured" if os.getenv("SENTRY_DSN") else "NOT SET",
    }
    import pandas as pd
    st.dataframe(pd.DataFrame(env_vars.items(), columns=["Key", "Value"]), use_container_width=True, hide_index=True)

    st.markdown("**API Health**")
    health = api_get("/health")
    if health:
        st.success(f"API online — {health.get('timestamp', '')}")
    else:
        st.error(f"API unreachable at {API}")
