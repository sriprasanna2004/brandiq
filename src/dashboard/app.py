import os
from datetime import datetime
import httpx
import streamlit as st

st.set_page_config(layout="wide", page_title="BrandIQ", page_icon="🎯", initial_sidebar_state="expanded")

API = os.getenv("API_URL", "https://brandiq-production-36b6.up.railway.app")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;}
.stApp{background:#07080f!important;color:#e8eaf6!important;}
.stApp>header{display:none!important;}
#MainMenu,footer,header{visibility:hidden!important;height:0!important;}
.block-container{padding:16px 20px 0 20px!important;max-width:100%!important;margin:0!important;}
section[data-testid="stSidebar"]{background:#0d0f1a!important;border-right:1px solid #1c1f32!important;min-width:210px!important;max-width:210px!important;}
section[data-testid="stSidebar"] .block-container{padding:16px 12px!important;}
section[data-testid="stSidebar"] *{color:#e8eaf6!important;}
section[data-testid="stSidebar"] .stRadio label{font-size:12px!important;padding:4px 0!important;}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"]{gap:2px!important;}
div[data-testid="metric-container"]{background:#0d0f1a!important;border:1px solid #1c1f32!important;border-radius:8px!important;padding:12px 14px!important;margin:0!important;}
div[data-testid="metric-container"] label{color:#4a4f72!important;font-family:'DM Mono',monospace!important;font-size:9px!important;letter-spacing:1.5px!important;text-transform:uppercase!important;}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{font-family:'Syne',sans-serif!important;font-size:24px!important;font-weight:800!important;color:#e8eaf6!important;line-height:1.1!important;}
div[data-testid="stHorizontalBlock"]{gap:8px!important;margin-bottom:8px!important;}
div[data-testid="column"]{padding:0!important;}
.stButton>button{background:#00e5c3!important;color:#000!important;font-weight:700!important;border:none!important;border-radius:6px!important;padding:5px 14px!important;font-size:11px!important;height:32px!important;width:100%!important;}
.stButton>button:hover{background:#00c9aa!important;}
.stButton>button[kind="secondary"]{background:#1c1f32!important;color:#e8eaf6!important;}
div[data-testid="stDataFrame"]{border:1px solid #1c1f32!important;border-radius:8px!important;}
div[data-testid="stDataFrame"] *{background:#0d0f1a!important;color:#e8eaf6!important;}
.stSelectbox>div>div{background:#0d0f1a!important;border:1px solid #1c1f32!important;color:#e8eaf6!important;border-radius:6px!important;font-size:12px!important;}
.stTextInput>div>div>input{background:#0d0f1a!important;border:1px solid #1c1f32!important;color:#e8eaf6!important;border-radius:6px!important;font-size:12px!important;}
.stForm{background:#0d0f1a!important;border:1px solid #1c1f32!important;border-radius:8px!important;padding:12px!important;}
.stMarkdown h3{font-family:'Syne',sans-serif!important;font-size:14px!important;font-weight:700!important;color:#e8eaf6!important;margin:0 0 8px 0!important;}
.stMarkdown p,.stMarkdown strong{font-size:12px!important;color:#e8eaf6!important;margin:0 0 4px 0!important;}
.stInfo,.stSuccess,.stError,.stWarning{font-size:11px!important;padding:8px 12px!important;border-radius:6px!important;}
hr{border-color:#1c1f32!important;margin:8px 0!important;}
.stDivider{margin:6px 0!important;}
div[data-testid="stVerticalBlock"]{gap:6px!important;}
.element-container{margin:0!important;padding:0!important;}
.stCaption{font-size:10px!important;color:#4a4f72!important;}
label[data-testid="stWidgetLabel"]{font-size:10px!important;color:#4a4f72!important;font-family:'DM Mono',monospace!important;letter-spacing:1px!important;text-transform:uppercase!important;margin-bottom:2px!important;}
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=30)
def api_get(path):
    try:
        r = httpx.get(f"{API}{path}", timeout=5)
        return r.json() if r.is_success else None
    except Exception:
        return None

def api_post(path, body={}):
    try:
        r = httpx.post(f"{API}{path}", json=body, timeout=10)
        return r.json() if r.is_success else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def badge(text, color):
    return f'<span style="background:{color}22;color:{color};border:1px solid {color}44;border-radius:4px;padding:2px 8px;font-family:DM Mono,monospace;font-size:9px;letter-spacing:.5px;font-weight:600">{text}</span>'

STATUS_COLOR = {"pending":"#ffd166","approved":"#4facfe","posted":"#00e5c3","failed":"#ff6b6b","running":"#ffd166","success":"#00e5c3","hot":"#ff6b6b","warm":"#ffd166","cold":"#4facfe","opted_out":"#4a4f72"}

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:20px;font-weight:800;color:#00e5c3;margin-bottom:2px">🎯 BrandIQ</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;letter-spacing:2px;margin-bottom:12px">TOPPER IAS · ADAPTIQ</div>', unsafe_allow_html=True)
    st.divider()
    page = st.radio("nav", ["Overview","Content Queue","Leads","Agent Jobs","Analytics","Settings"], label_visibility="collapsed")
    st.divider()
    st.markdown('<div style="font-size:10px;color:#4a4f72;font-family:DM Mono,monospace;letter-spacing:1px;margin-bottom:6px">QUICK ACTIONS</div>', unsafe_allow_html=True)
    if st.button("▶ Run Content Crew"):
        res = api_post("/tasks/content")
        st.success(f"Queued ✓") if res and "task_id" in res else st.error(str(res))
    if st.button("▶ Run Analytics"):
        res = api_post("/tasks/analytics")
        st.success(f"Queued ✓") if res and "task_id" in res else st.error(str(res))
    if st.button("🔄 Refresh"):
        st.cache_data.clear(); st.rerun()
    st.divider()
    health = api_get("/health")
    dot = "🟢" if health else "🔴"
    st.markdown(f'<div style="font-size:11px">{dot} API {"Online" if health else "Offline"}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:9px;color:#4a4f72;font-family:DM Mono,monospace">{datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

# ── KPI Row ───────────────────────────────────────────────────────────────────
kpis = api_get("/stats/kpis") or {}
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("📸 Posts Today",   kpis.get("posts_today",0))
c2.metric("👤 New Leads",     kpis.get("new_leads",0))
c3.metric("🔥 Hot Leads",     kpis.get("hot_leads",0))
c4.metric("💬 WhatsApp Sent", kpis.get("wa_sent",0))
c5.metric("📱 Adaptiq Trials",kpis.get("trials_today",0))
st.divider()

# ── Pages ─────────────────────────────────────────────────────────────────────
if page == "Overview":
    col_a, col_b = st.columns([1,2])
    with col_a:
        st.markdown("### 📊 Totals")
        ca, cb = st.columns(2)
        ca.metric("Total Posts", kpis.get("total_posts",0))
        cb.metric("Total Leads", kpis.get("total_leads",0))
        st.markdown("### ⚡ Trigger Lead")
        with st.form("lead_form", clear_on_submit=True):
            ig = st.text_input("Instagram Handle", placeholder="@username")
            msg = st.text_input("Message", placeholder="what are the fees?")
            day = st.selectbox("Day", [0,1,3,7,14], help="0=score new lead, 1/3/7/14=nurture")
            if st.form_submit_button("Send →"):
                res = api_post("/tasks/lead", {"ig_handle": ig.lstrip("@"), "message_text": msg, "day_number": day})
                st.success("Queued ✓") if res and "task_id" in res else st.error(str(res))
    with col_b:
        st.markdown("### 🤖 Recent Agent Jobs")
        jobs = api_get("/stats/agent-jobs") or []
        if jobs:
            for j in jobs[:10]:
                c = STATUS_COLOR.get(j["status"], "#4a4f72")
                ts = (j.get("created_at") or "")[:16].replace("T"," ")
                st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #1c1f32"><span style="font-size:11px;font-weight:600;width:130px;flex-shrink:0">{j["agent_name"]}</span>{badge(j["status"].upper(),c)}<span style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;margin-left:auto">{ts}</span></div>', unsafe_allow_html=True)
        else:
            st.info("No agent jobs yet — trigger a crew from the sidebar.")

elif page == "Content Queue":
    st.markdown("### 📅 Content Queue")
    col_f, _ = st.columns([1,3])
    sf = col_f.selectbox("Status", ["all","pending","approved","posted","failed"], label_visibility="collapsed")
    posts = api_get(f"/posts?status={sf}&limit=30") if sf != "all" else api_get("/posts?limit=30")
    posts = posts or []
    if not posts:
        st.info("No posts found. Run the Content Crew to generate posts.")
    else:
        st.markdown(f'<div style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;margin-bottom:6px">{len(posts)} POSTS</div>', unsafe_allow_html=True)
        for p in posts:
            c = STATUS_COLOR.get(p["status"], "#4a4f72")
            sched = (p.get("scheduled_at") or "—")[:16].replace("T"," ")
            col1,col2,col3,col4,col5 = st.columns([4,1,1,1,1])
            col1.markdown(f'<div style="font-size:11px;font-weight:600;padding:6px 0">{p["caption_a"][:65]}…</div>', unsafe_allow_html=True)
            col2.markdown(f'<div style="padding:6px 0;font-size:10px;color:#4a4f72">{p["platform"]}</div>', unsafe_allow_html=True)
            col3.markdown(f'<div style="padding:6px 0">{badge(p["status"].upper(),c)}</div>', unsafe_allow_html=True)
            col4.markdown(f'<div style="padding:6px 0;font-family:DM Mono,monospace;font-size:9px;color:#4a4f72">{sched}</div>', unsafe_allow_html=True)
            if p["status"] == "pending":
                if col5.button("✅", key=f"a_{p['id']}", help="Approve"):
                    api_post("/posts/approve", {"post_id": p["id"]}); st.cache_data.clear(); st.rerun()
            elif p["status"] == "approved":
                if col5.button("🚀", key=f"p_{p['id']}", help="Publish now"):
                    api_post(f"/posts/publish/{p['id']}"); st.cache_data.clear(); st.rerun()
            st.markdown('<hr style="margin:0;border-color:#1c1f32">', unsafe_allow_html=True)

elif page == "Leads":
    st.markdown("### 👥 Leads")
    col_f, col_n = st.columns([1,3])
    sf = col_f.selectbox("Status", ["all","hot","warm","cold","opted_out"], label_visibility="collapsed")
    leads = api_get(f"/leads?status={sf}&limit=50") if sf != "all" else api_get("/leads?limit=50")
    leads = leads or []
    if not leads:
        st.info("No leads yet. Leads are captured automatically from Instagram DMs.")
    else:
        st.markdown(f'<div style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;margin-bottom:6px">{len(leads)} LEADS</div>', unsafe_allow_html=True)
        for l in leads:
            c = STATUS_COLOR.get(l["status"], "#4a4f72")
            ts = (l.get("created_at") or "")[:10]
            c1,c2,c3,c4,c5 = st.columns([2,2,2,1,1])
            c1.markdown(f'<div style="font-size:11px;font-weight:600;padding:5px 0">@{l["ig_handle"]}</div>', unsafe_allow_html=True)
            c2.markdown(f'<div style="font-size:11px;padding:5px 0;color:#4a4f72">{l.get("name") or "—"}</div>', unsafe_allow_html=True)
            c3.markdown(f'<div style="font-size:11px;padding:5px 0;color:#4a4f72">{l.get("phone") or "—"}</div>', unsafe_allow_html=True)
            c4.markdown(f'<div style="padding:5px 0">{badge(l["status"].upper(),c)}</div>', unsafe_allow_html=True)
            c5.markdown(f'<div style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;padding:5px 0">{ts}</div>', unsafe_allow_html=True)
            st.markdown('<hr style="margin:0;border-color:#1c1f32">', unsafe_allow_html=True)
        st.markdown("### 💬 Send Nurture")
        with st.form("nurture"):
            handles = [l["ig_handle"] for l in leads]
            c1,c2,c3 = st.columns([2,1,1])
            sel = c1.selectbox("Lead", handles, label_visibility="collapsed")
            day_n = c2.selectbox("Day", [1,3,7,14], label_visibility="collapsed")
            if c3.form_submit_button("Send →"):
                res = api_post("/tasks/lead", {"ig_handle": sel, "message_text": "", "day_number": day_n})
                st.success("Queued ✓") if res else st.error("Failed")

elif page == "Agent Jobs":
    st.markdown("### 🤖 Agent Job Log")
    jobs = api_get("/stats/agent-jobs") or []
    if not jobs:
        st.info("No jobs yet.")
    else:
        st.markdown(f'<div style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;margin-bottom:6px">{len(jobs)} JOBS</div>', unsafe_allow_html=True)
        for j in jobs:
            c = STATUS_COLOR.get(j["status"], "#4a4f72")
            ts = (j.get("created_at") or "")[:16].replace("T"," ")
            err = f' — <span style="color:#ff6b6b;font-size:9px">{str(j.get("error") or "")[:60]}</span>' if j.get("error") else ""
            st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #1c1f32"><span style="font-size:11px;font-weight:600;width:140px;flex-shrink:0">{j["agent_name"]}</span>{badge(j["status"].upper(),c)}<span style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{j["job_id"]}</span><span style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;margin-left:auto;flex-shrink:0">{ts}</span>{err}</div>', unsafe_allow_html=True)

elif page == "Analytics":
    st.markdown("### 📊 Analytics")
    import json
    redis_url = os.getenv("REDIS_URL","")
    summary = None
    if redis_url:
        try:
            import redis as rl
            r = rl.from_url(redis_url, decode_responses=True, socket_connect_timeout=3)
            raw = r.get("analytics:weekly_summary")
            if raw: summary = json.loads(raw)
        except Exception: pass
    if summary:
        c1,c2 = st.columns(2)
        c1.metric("Weekly Reach", f'{summary.get("weekly_reach_total",0):,}')
        c2.metric("Leads Generated", summary.get("weekly_leads_generated",0))
        st.markdown("**Insight**")
        st.info(summary.get("insight_text",""))
        mix = summary.get("recommended_content_mix",{})
        if mix:
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(x=list(mix.keys()), y=list(mix.values()), marker_color=["#00e5c3","#4facfe","#ffd166","#ff6b6b","#9d6fff"]))
            fig.update_layout(paper_bgcolor="#07080f",plot_bgcolor="#0d0f1a",font_color="#e8eaf6",height=220,margin=dict(l=10,r=10,t=10,b=10),showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No analytics data yet — runs nightly at 11 PM.")
    if st.button("▶ Run Analytics Now"):
        res = api_post("/tasks/analytics"); st.success(f"Queued ✓") if res else st.error("Failed")

elif page == "Settings":
    st.markdown("### ⚙️ Settings")
    keys = {"API_URL": API, "ENVIRONMENT": os.getenv("ENVIRONMENT","—"), "ANTHROPIC_API_KEY": "✓ set" if os.getenv("ANTHROPIC_API_KEY") else "✗ NOT SET", "META_ACCESS_TOKEN": "✓ set" if os.getenv("META_ACCESS_TOKEN") else "✗ NOT SET", "TELEGRAM_BOT_TOKEN": "✓ set" if os.getenv("TELEGRAM_BOT_TOKEN") else "✗ NOT SET", "WHATSAPP_PHONE_NUMBER_ID": os.getenv("WHATSAPP_PHONE_NUMBER_ID","✗ NOT SET"), "STABILITY_API_KEY": "✓ set" if os.getenv("STABILITY_API_KEY") else "✗ NOT SET", "SENTRY_DSN": "✓ set" if os.getenv("SENTRY_DSN") else "✗ NOT SET"}
    for k,v in keys.items():
        ok = "✗" not in str(v)
        c = "#00e5c3" if ok else "#ff6b6b"
        st.markdown(f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1c1f32;font-size:11px"><span style="font-family:DM Mono,monospace;color:#4a4f72">{k}</span><span style="color:{c}">{v}</span></div>', unsafe_allow_html=True)
    st.markdown('<div style="margin-top:12px"></div>', unsafe_allow_html=True)
    health = api_get("/health")
    if health: st.success(f"API online — {health.get('timestamp','')[:19]}")
    else: st.error(f"API unreachable at {API}")
