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
.block-container{padding:14px 18px 0 18px!important;max-width:100%!important;margin:0!important;}
section[data-testid="stSidebar"]{background:#0d0f1a!important;border-right:1px solid #1c1f32!important;min-width:200px!important;max-width:200px!important;}
section[data-testid="stSidebar"] .block-container{padding:14px 10px!important;}
section[data-testid="stSidebar"] *{color:#e8eaf6!important;}
section[data-testid="stSidebar"] .stRadio label{font-size:12px!important;padding:3px 0!important;}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"]{gap:1px!important;}
div[data-testid="metric-container"]{background:#0d0f1a!important;border:1px solid #1c1f32!important;border-radius:8px!important;padding:10px 12px!important;margin:0!important;}
div[data-testid="metric-container"] label{color:#4a4f72!important;font-family:'DM Mono',monospace!important;font-size:9px!important;letter-spacing:1.5px!important;text-transform:uppercase!important;}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{font-family:'Syne',sans-serif!important;font-size:22px!important;font-weight:800!important;color:#e8eaf6!important;line-height:1.1!important;}
div[data-testid="stHorizontalBlock"]{gap:8px!important;margin-bottom:8px!important;}
div[data-testid="column"]{padding:0!important;}
.stButton>button{background:#00e5c3!important;color:#000!important;font-weight:700!important;border:none!important;border-radius:6px!important;padding:4px 12px!important;font-size:11px!important;height:28px!important;width:100%!important;}
.stButton>button:hover{background:#00c9aa!important;}
div[data-testid="stVerticalBlock"]{gap:4px!important;}
.element-container{margin:0!important;padding:0!important;}
hr{border-color:#1c1f32!important;margin:6px 0!important;}
.stSelectbox>div>div{background:#0d0f1a!important;border:1px solid #1c1f32!important;color:#e8eaf6!important;border-radius:6px!important;font-size:11px!important;}
.stTextInput>div>div>input{background:#0d0f1a!important;border:1px solid #1c1f32!important;color:#e8eaf6!important;border-radius:6px!important;font-size:11px!important;}
.stForm{background:#0d0f1a!important;border:1px solid #1c1f32!important;border-radius:8px!important;padding:10px!important;}
label[data-testid="stWidgetLabel"]{font-size:9px!important;color:#4a4f72!important;font-family:'DM Mono',monospace!important;letter-spacing:1px!important;text-transform:uppercase!important;margin-bottom:2px!important;}
</style>""", unsafe_allow_html=True)

# ── helpers ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=20)
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

SC = {"hot":"#ff6b6b","warm":"#ffd166","cold":"#4facfe","opted_out":"#4a4f72",
      "pending":"#ffd166","approved":"#4facfe","posted":"#00e5c3","failed":"#ff6b6b",
      "success":"#00e5c3","running":"#ffd166","dead_letter":"#ff6b6b"}

def badge(t, c="#4a4f72"):
    return f'<span style="background:{c}18;color:{c};border:1px solid {c}33;border-radius:3px;padding:1px 7px;font-family:DM Mono,monospace;font-size:9px;letter-spacing:.5px;font-weight:600">{t}</span>'

def panel(title, meta="", body_html=""):
    return f'''<div style="background:#0d0f1a;border:1px solid #1c1f32;border-radius:10px;overflow:hidden;height:100%">
<div style="padding:10px 14px;border-bottom:1px solid #1c1f32;display:flex;justify-content:space-between;align-items:center">
<span style="font-family:Syne,sans-serif;font-size:12px;font-weight:700">{title}</span>
<span style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72">{meta}</span></div>
<div style="padding:10px 14px">{body_html}</div></div>'''

def row_html(items):
    return "".join(f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #1c1f32">{i}</div>' for i in items)

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:18px;font-weight:800;color:#00e5c3;margin-bottom:1px">🎯 BrandIQ</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;letter-spacing:2px;margin-bottom:10px">TOPPER IAS · ADAPTIQ</div>', unsafe_allow_html=True)
    st.divider()
    page = st.radio("nav", ["Overview","Content Queue","Leads","Agent Jobs","Analytics","Settings"], label_visibility="collapsed")
    st.divider()
    st.markdown('<div style="font-size:9px;color:#4a4f72;font-family:DM Mono,monospace;letter-spacing:1px;margin-bottom:4px">QUICK ACTIONS</div>', unsafe_allow_html=True)
    if st.button("▶ Run Content Crew"):
        res = api_post("/tasks/content")
        st.success("Queued ✓") if res and "task_id" in res else st.error(str(res))
    if st.button("▶ Run Analytics"):
        res = api_post("/tasks/analytics")
        st.success("Queued ✓") if res and "task_id" in res else st.error(str(res))
    if st.button("🔄 Refresh"):
        st.cache_data.clear(); st.rerun()
    st.divider()
    health = api_get("/health")
    st.markdown(f'<div style="font-size:11px">{"🟢" if health else "🔴"} API {"Online" if health else "Offline"}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:9px;color:#4a4f72;font-family:DM Mono,monospace">{datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────
kpis = api_get("/stats/kpis") or {}
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("📸 Posts Today",   kpis.get("posts_today",0))
c2.metric("👤 New Leads",     kpis.get("new_leads",0))
c3.metric("🔥 Hot Leads",     kpis.get("hot_leads",0))
c4.metric("💬 WhatsApp Sent", kpis.get("wa_sent",0))
c5.metric("📱 Adaptiq Trials",kpis.get("trials_today",0))
st.divider()

# ── OVERVIEW ─────────────────────────────────────────────────────────────────
if page == "Overview":
    # Row 1: Agent Status | Content Queue | Lead Pipeline
    col1, col2, col3 = st.columns([1.1, 1.4, 1.1])

    # Agent Status
    AGENT_DEFS = [
        ("StrategyAgent","Planning content...","#00e5c3","RUN"),
        ("ContentWriter","Writing captions","#ffd166","WRITE"),
        ("VisualCreator","Generating image","#4facfe","GEN"),
        ("SchedulerAgent","Optimising times","#00e5c3","IDLE"),
        ("LeadCapture","Monitoring DMs","#00e5c3","SCAN"),
        ("LeadNurture","Sending sequences","#ffd166","SEND"),
        ("ReelScript","Drafting script","#4facfe","DRAFT"),
        ("Analytics","Insights pulled ✓","#00e5c3","DONE"),
        ("AdaptiqPromo","Trial msgs sent","#00e5c3","RUN"),
    ]
    agent_jobs = api_get("/stats/agent-status") or []
    job_map = {j["agent_name"]: j for j in agent_jobs}
    rows = []
    for name, default_task, default_color, default_badge in AGENT_DEFS:
        job = job_map.get(name, {})
        status = job.get("status", "idle")
        c = SC.get(status, default_color)
        dot_anim = "animation:pulse 1.5s infinite;" if status == "running" else ""
        rows.append(
            f'<div style="width:6px;height:6px;border-radius:50%;background:{c};flex-shrink:0;{dot_anim}"></div>'
            f'<span style="font-weight:600;width:88px;flex-shrink:0;font-size:11px">{name}</span>'
            f'<span style="color:#4a4f72;flex:1;font-size:10px;font-family:DM Mono,monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{default_task}</span>'
            f'{badge(default_badge, c)}'
        )
    agent_html = "".join(f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #1c1f32">{r}</div>' for r in rows)
    with col1:
        st.markdown(panel("Agent Status", "9/9 ACTIVE", agent_html), unsafe_allow_html=True)

    # Content Queue
    posts = api_get("/posts?limit=6") or []
    ICONS = {"reel":"🧠","carousel":"📊","story":"🎯","post":"✍️","whatsapp":"💬"}
    STATUS_CSS = {"posted":"ps-live","approved":"ps-live","pending":"ps-dft","failed":"ps-dft"}
    STATUS_LBL = {"posted":"LIVE","approved":"SCHED","pending":"DRAFT","failed":"FAIL"}
    post_rows = ""
    for p in posts:
        icon = ICONS.get(p.get("platform","post"), "📝")
        sc = STATUS_CSS.get(p["status"], "ps-dft")
        sl = STATUS_LBL.get(p["status"], p["status"].upper())
        sched = (p.get("scheduled_at") or "")[:16].replace("T"," ")
        post_rows += f'''<div style="display:flex;gap:8px;padding:7px 0;border-bottom:1px solid #1c1f32;align-items:center">
<div style="width:32px;height:32px;border-radius:7px;background:#9d6fff18;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0">{icon}</div>
<div style="flex:1;min-width:0"><div style="font-size:11px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{p["caption_a"][:45]}…</div>
<div style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72">{p["platform"].upper()} · {sched}</div></div>
{badge(sl, "#00e5c3" if sl=="LIVE" else "#4facfe" if sl=="SCHED" else "#ffd166")}</div>'''
    if not post_rows:
        post_rows = '<div style="color:#4a4f72;font-size:11px;padding:10px 0">No posts yet — run Content Crew</div>'
    with col2:
        st.markdown(panel("Content Queue", f"{len(posts)} TODAY", post_rows), unsafe_allow_html=True)

    # Lead Pipeline
    leads = api_get("/leads?limit=7") or []
    lead_rows = ""
    for l in leads:
        initials = "".join(w[0].upper() for w in (l.get("name") or l["ig_handle"]).split()[:2])
        c = SC.get(l["status"], "#4a4f72")
        age = ""
        if l.get("created_at"):
            try:
                from datetime import timezone, timedelta
                dt = datetime.fromisoformat(l["created_at"].replace("Z","+00:00"))
                age = f'D{(datetime.now(timezone.utc)-dt).days+1}'
            except Exception:
                pass
        lead_rows += f'''<div style="display:flex;align-items:center;gap:7px;padding:5px 0;border-bottom:1px solid #1c1f32">
<div style="width:26px;height:26px;border-radius:6px;background:{c}18;color:{c};display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;flex-shrink:0">{initials}</div>
<div style="flex:1;min-width:0"><div style="font-size:11px;font-weight:600">{l.get("name") or "@"+l["ig_handle"]}</div>
<div style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{l.get("source","").replace("_"," ")}</div></div>
{badge(l["status"].upper(), c)}
<span style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;width:24px;text-align:right">{age}</span></div>'''
    if not lead_rows:
        lead_rows = '<div style="color:#4a4f72;font-size:11px;padding:10px 0">No leads yet</div>'
    with col3:
        st.markdown(panel("Lead Pipeline", f"{kpis.get('new_leads',0)} TODAY", lead_rows), unsafe_allow_html=True)

    st.markdown('<div style="margin-top:8px"></div>', unsafe_allow_html=True)

    # Row 2: Reach Chart | Lead Funnel | Adaptiq Funnel | Revenue+Feed
    col4, col5, col6, col7 = st.columns([1.6, 1, 1, 0.9])

    # Weekly Reach
    reach_data = api_get("/stats/reach") or []
    if reach_data:
        import plotly.graph_objects as go
        fig = go.Figure(go.Bar(
            x=[r["day"] for r in reach_data],
            y=[r["reach"] for r in reach_data],
            marker=dict(color=["#00e5c3"]*len(reach_data), opacity=[0.4+0.1*i for i in range(len(reach_data))]),
        ))
        fig.update_layout(paper_bgcolor="#0d0f1a", plot_bgcolor="#0d0f1a", font_color="#e8eaf6",
            height=130, margin=dict(l=0,r=0,t=0,b=0), showlegend=False,
            xaxis=dict(showgrid=False, tickfont=dict(size=9, family="DM Mono")),
            yaxis=dict(showgrid=False, showticklabels=False))
        with col4:
            st.markdown('<div style="background:#0d0f1a;border:1px solid #1c1f32;border-radius:10px;padding:10px 14px"><div style="font-family:Syne,sans-serif;font-size:12px;font-weight:700;margin-bottom:6px">Weekly Reach <span style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;font-weight:400">LAST 7 DAYS</span></div>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        with col4:
            st.markdown(panel("Weekly Reach", "LAST 7 DAYS", '<div style="color:#4a4f72;font-size:11px;padding:20px 0;text-align:center">No reach data yet</div>'), unsafe_allow_html=True)

    # Funnels
    funnels = api_get("/stats/funnels") or {}
    FUNNEL_COLORS = ["#9d6fff","#4facfe","#00e5c3","#ffd166","#ff6b6b"]

    def funnel_html(steps, colors):
        html = ""
        for i, s in enumerate(steps):
            v = s["value"]
            label = f'{v:,}' if isinstance(v, int) and v > 999 else str(v)
            html += f'''<div style="margin-bottom:7px">
<div style="display:flex;justify-content:space-between;margin-bottom:2px;font-size:10px">
<span style="color:#4a4f72">{s["label"]}</span><span style="font-family:DM Mono,monospace;font-weight:700">{label}</span></div>
<div style="background:#1c1f32;border-radius:2px;height:4px"><div style="height:4px;border-radius:2px;width:{s["pct"]}%;background:{colors[i]}"></div></div></div>'''
        return html

    with col5:
        lf = funnels.get("lead_funnel", [{"label":"Reached","value":0,"pct":100},{"label":"Engaged","value":0,"pct":75},{"label":"Enquired","value":0,"pct":48},{"label":"Trial","value":0,"pct":28},{"label":"Admitted","value":0,"pct":12}])
        st.markdown(panel("Lead Funnel", "THIS MONTH", funnel_html(lf, FUNNEL_COLORS)), unsafe_allow_html=True)

    with col6:
        af = funnels.get("adaptiq_funnel", [{"label":"Promo Views","value":0,"pct":100},{"label":"Link Clicks","value":0,"pct":70},{"label":"Free Trial","value":0,"pct":42},{"label":"Day 5 Active","value":0,"pct":26},{"label":"Converted","value":0,"pct":10}])
        st.markdown(panel("Adaptiq Funnel", "THIS MONTH", funnel_html(af, ["#00e5c3"]*5)), unsafe_allow_html=True)

    # Revenue + Live Feed
    live_feed = api_get("/stats/live-feed") or []
    feed_html = ""
    for e in live_feed[:4]:
        ts = ""
        if e.get("time"):
            try:
                from datetime import timezone
                dt = datetime.fromisoformat(e["time"].replace("Z","+00:00"))
                mins = int((datetime.now(timezone.utc)-dt).total_seconds()//60)
                ts = f"{mins}m ago" if mins < 60 else f"{mins//60}h ago"
            except Exception:
                pass
        feed_html += f'''<div style="display:flex;gap:7px;padding:6px 0;border-bottom:1px solid #1c1f32;align-items:flex-start">
<div style="width:22px;height:22px;border-radius:5px;background:{e.get("color","#4a4f72")}18;display:flex;align-items:center;justify-content:center;font-size:10px;flex-shrink:0">{e.get("icon","•")}</div>
<div><div style="font-size:10px;line-height:1.4">{e.get("text","")}</div>
<div style="font-family:DM Mono,monospace;font-size:8px;color:#4a4f72;margin-top:1px">{ts}</div></div></div>'''
    if not feed_html:
        feed_html = '<div style="color:#4a4f72;font-size:11px;padding:8px 0">No recent activity</div>'

    rev_html = f'''<div style="background:#111320;border:1px solid #1c1f32;border-radius:8px;padding:12px;border-top:2px solid #00e5c3;margin-bottom:8px">
<div style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px">Revenue · This Month</div>
<div style="font-family:Syne,sans-serif;font-size:22px;font-weight:800;color:#00e5c3;letter-spacing:-1px">₹{kpis.get("total_posts",0)*1500:,}</div>
<div style="font-size:10px;color:#4a4f72;margin-top:2px">Based on {kpis.get("total_posts",0)} posts published</div>
<div style="display:flex;gap:6px;margin-top:8px">
<div style="flex:1;background:#ffffff06;border-radius:5px;padding:7px;border:1px solid #1c1f32"><div style="font-family:DM Mono,monospace;font-size:8px;color:#4a4f72;margin-bottom:2px">TOPPER IAS</div><div style="font-family:Syne,sans-serif;font-size:12px;font-weight:700;color:#9d6fff">₹{kpis.get("hot_leads",0)*25000:,}</div></div>
<div style="flex:1;background:#ffffff06;border-radius:5px;padding:7px;border:1px solid #1c1f32"><div style="font-family:DM Mono,monospace;font-size:8px;color:#4a4f72;margin-bottom:2px">ADAPTIQ</div><div style="font-family:Syne,sans-serif;font-size:12px;font-weight:700;color:#00e5c3">₹{kpis.get("trials_today",0)*299:,}</div></div></div></div>'''

    with col7:
        st.markdown(rev_html, unsafe_allow_html=True)
        st.markdown(panel("Live Feed", "NOW", feed_html), unsafe_allow_html=True)

    # Row 3: Content Calendar
    st.markdown('<div style="margin-top:8px"></div>', unsafe_allow_html=True)
    calendar = api_get("/calendar") or {}
    from datetime import timezone, timedelta
    today = datetime.now(timezone.utc)
    week_start = today - timedelta(days=today.weekday())
    days = [(week_start + timedelta(days=i)) for i in range(7)]
    DAY_NAMES = ["MON","TUE","WED","THU","FRI","SAT","SUN"]
    TYPE_COLORS = {"reel":"#9d6fff","carousel":"#00e5c3","story":"#4facfe","post":"#ffd166","whatsapp":"#ff6b6b"}

    cal_html = '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:5px">'
    for d in DAY_NAMES:
        cal_html += f'<div style="font-family:DM Mono,monospace;font-size:8px;color:#4a4f72;text-align:center;padding:3px;letter-spacing:1px">{d}</div>'
    for day in days:
        key = day.strftime("%Y-%m-%d")
        is_today = key == today.strftime("%Y-%m-%d")
        border = "#00e5c3" if is_today else "#1c1f32"
        bg = "#00e5c305" if is_today else "#111320"
        num_color = "#00e5c3" if is_today else "#4a4f72"
        dot = " ●" if is_today else ""
        events = calendar.get(key, [])
        events_html = ""
        for e in events[:3]:
            c = TYPE_COLORS.get(e.get("platform","post"), "#4a4f72")
            events_html += f'<div style="border-radius:3px;padding:2px 4px;margin-bottom:2px;font-size:8px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:DM Mono,monospace;background:{c}18;color:{c}">{e["caption"][:18]}</div>'
        cal_html += f'<div style="background:{bg};border:1px solid {border};border-radius:6px;padding:6px;min-height:56px"><div style="font-family:DM Mono,monospace;font-size:9px;color:{num_color};margin-bottom:3px;font-weight:500">{day.day}{dot}</div>{events_html}</div>'
    cal_html += '</div>'

    st.markdown(f'''<div style="background:#0d0f1a;border:1px solid #1c1f32;border-radius:10px;overflow:hidden">
<div style="padding:10px 14px;border-bottom:1px solid #1c1f32;display:flex;justify-content:space-between;align-items:center">
<span style="font-family:Syne,sans-serif;font-size:12px;font-weight:700">Content Calendar — This Week</span>
<span style="font-family:DM Mono,monospace;font-size:9px;color:#4a4f72">AUTO-GENERATED BY STRATEGYAGENT</span></div>
<div style="padding:10px 14px">{cal_html}</div></div>''', unsafe_allow_html=True)

# ── OTHER PAGES ───────────────────────────────────────────────────────────────
elif page == "Content Queue":
    st.markdown("### 📅 Content Queue")
    sf = st.selectbox("Status", ["all","pending","approved","posted","failed"], label_visibility="collapsed")
    posts = api_get(f"/posts?status={sf}&limit=30") if sf != "all" else api_get("/posts?limit=30")
    posts = posts or []
    if not posts:
        st.markdown('<div style="color:#4a4f72;font-size:12px;padding:20px 0">No posts found. Run Content Crew to generate posts.</div>', unsafe_allow_html=True)
    else:
        for p in posts:
            c = SC.get(p["status"], "#4a4f72")
            sched = (p.get("scheduled_at") or "—")[:16].replace("T"," ")
            col1,col2,col3,col4,col5 = st.columns([4,1,1,1,1])
            col1.markdown(f'<div style="font-size:11px;font-weight:600;padding:5px 0">{p["caption_a"][:65]}…</div>', unsafe_allow_html=True)
            col2.markdown(f'<div style="padding:5px 0;font-size:10px;color:#4a4f72">{p["platform"]}</div>', unsafe_allow_html=True)
            col3.markdown(f'<div style="padding:5px 0">{badge(p["status"].upper(),c)}</div>', unsafe_allow_html=True)
            col4.markdown(f'<div style="padding:5px 0;font-family:DM Mono,monospace;font-size:9px;color:#4a4f72">{sched}</div>', unsafe_allow_html=True)
            if p["status"] == "pending":
                if col5.button("✅", key=f"a_{p['id']}", help="Approve"):
                    api_post("/posts/approve", {"post_id": p["id"]}); st.cache_data.clear(); st.rerun()
            elif p["status"] == "approved":
                if col5.button("🚀", key=f"p_{p['id']}", help="Publish now"):
                    api_post(f"/posts/publish/{p['id']}"); st.cache_data.clear(); st.rerun()
            st.markdown('<hr style="margin:0;border-color:#1c1f32">', unsafe_allow_html=True)

elif page == "Leads":
    st.markdown("### 👥 Leads")
    sf = st.selectbox("Status", ["all","hot","warm","cold","opted_out"], label_visibility="collapsed")
    leads = api_get(f"/leads?status={sf}&limit=50") if sf != "all" else api_get("/leads?limit=50")
    leads = leads or []
    if not leads:
        st.markdown('<div style="color:#4a4f72;font-size:12px;padding:20px 0">No leads yet. Leads are captured automatically from Instagram DMs.</div>', unsafe_allow_html=True)
    else:
        for l in leads:
            c = SC.get(l["status"], "#4a4f72")
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
        st.markdown('<div style="color:#4a4f72;font-size:12px;padding:20px 0">No jobs yet.</div>', unsafe_allow_html=True)
    else:
        for j in jobs:
            c = SC.get(j["status"], "#4a4f72")
            ts = (j.get("created_at") or "")[:16].replace("T"," ")
            err = f'<span style="color:#ff6b6b;font-size:9px;font-family:DM Mono,monospace"> — {str(j.get("error") or "")[:50]}</span>' if j.get("error") else ""
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
        res = api_post("/tasks/analytics"); st.success("Queued ✓") if res else st.error("Failed")

elif page == "Settings":
    st.markdown("### ⚙️ Settings")
    keys = {"API_URL": API, "ENVIRONMENT": os.getenv("ENVIRONMENT","—"), "GROQ_API_KEY": "✓ set" if os.getenv("GROQ_API_KEY") else "✗ NOT SET", "META_ACCESS_TOKEN": "✓ set" if os.getenv("META_ACCESS_TOKEN") else "✗ NOT SET", "TELEGRAM_BOT_TOKEN": "✓ set" if os.getenv("TELEGRAM_BOT_TOKEN") else "✗ NOT SET", "WHATSAPP_PHONE_NUMBER_ID": os.getenv("WHATSAPP_PHONE_NUMBER_ID","✗ NOT SET"), "STABILITY_API_KEY": "✓ set" if os.getenv("STABILITY_API_KEY") else "✗ NOT SET"}
    for k,v in keys.items():
        ok = "✗" not in str(v)
        c = "#00e5c3" if ok else "#ff6b6b"
        st.markdown(f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1c1f32;font-size:11px"><span style="font-family:DM Mono,monospace;color:#4a4f72">{k}</span><span style="color:{c}">{v}</span></div>', unsafe_allow_html=True)
    health = api_get("/health")
    st.markdown('<div style="margin-top:10px"></div>', unsafe_allow_html=True)
    if health: st.success(f"API online — {health.get('timestamp','')[:19]}")
    else: st.error(f"API unreachable at {API}")
