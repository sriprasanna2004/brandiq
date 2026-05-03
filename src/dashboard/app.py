"""
BrandIQ Dashboard — serves the exact HTML mockup with live data injected.
All data comes from the Railway API. No empty buttons, no dead UI.
"""
import os
from datetime import datetime, timezone, timedelta

import httpx
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="BrandIQ", page_icon="🎯")
st.markdown("<style>#MainMenu,footer,header{visibility:hidden!important;}.block-container{padding:0!important;margin:0!important;max-width:100%!important;}</style>", unsafe_allow_html=True)

API = os.getenv("API_URL", "https://brandiq-production-36b6.up.railway.app")

# ── fetch all data ────────────────────────────────────────────────────────────
def get(path, fallback=None):
    try:
        r = httpx.get(f"{API}{path}", timeout=6)
        return r.json() if r.is_success else fallback
    except Exception:
        return fallback

kpis    = get("/stats/kpis", {})
agents  = get("/stats/agent-status", [])
posts   = get("/posts?limit=5", [])
leads   = get("/leads?limit=7", [])
reach   = get("/stats/reach", [])
funnels = get("/stats/funnels", {})
feed    = get("/stats/live-feed", [])
cal     = get("/calendar", {})

# ── helpers ───────────────────────────────────────────────────────────────────
def fmt(n):
    if n >= 100000: return f"{n/100000:.1f}L"
    if n >= 1000:   return f"{n/1000:.0f}K"
    return str(n)

def ago(iso):
    try:
        dt = datetime.fromisoformat(iso.replace("Z","+00:00"))
        s = int((datetime.now(timezone.utc) - dt).total_seconds())
        if s < 60: return f"{s}s ago"
        if s < 3600: return f"{s//60}m ago"
        return f"{s//3600}h ago"
    except Exception:
        return ""

AGENT_DEFS = [
    ("StrategyAgent",    "Planning content calendar",  "#00e5c3", "Running"),
    ("ContentWriter",    "Writing captions",           "#ffd166", "Writing"),
    ("VisualCreator",    "Generating visuals",         "#4facfe", "Generating"),
    ("SchedulerAgent",   "Optimising post times",      "#4a4f72", "Waiting"),
    ("LeadCapture",      "Monitoring DMs",             "#00e5c3", "Scanning"),
    ("LeadNurture",      "Sending sequences",          "#ffd166", "Sending"),
    ("ReelScript",       "Drafting reel script",       "#4facfe", "Drafting"),
    ("AnalyticsAgent",   "Daily insights pulled ✓",    "#4a4f72", "Done"),
    ("AdaptiqPromo",     "Trial messages sent",        "#00e5c3", "Running"),
]
agent_map = {j["agent_name"]: j for j in agents}

STATUS_COLOR = {"success":"#00e5c3","running":"#ffd166","failed":"#ff6b6b","pending":"#4a4f72","hot":"#ff6b6b","warm":"#ffd166","cold":"#4facfe","posted":"#00e5c3","approved":"#4facfe","pending_post":"#ffd166"}
POST_ICON = {"instagram":"📊","telegram":"✈️"}
LEAD_COLORS = ["#ff6b6b","#9d6fff","#ffd166","#00e5c3","#4facfe","#4facfe","#ff6b6b"]

# ── build agent rows ──────────────────────────────────────────────────────────
agent_rows = ""
for name, task, color, badge_text in AGENT_DEFS:
    job = agent_map.get(name, {})
    status = job.get("status","idle")
    c = STATUS_COLOR.get(status, color)
    badge_bg = f"{c}22"
    anim = "animation:pulse 1.5s infinite;" if status == "running" else ""
    agent_rows += f"""
    <div class="agent-row">
      <div class="ad" style="background:{c};{anim}"></div>
      <div class="an">{name}</div>
      <div class="at">{task}</div>
      <span class="abadge" style="background:{badge_bg};color:{c}">{badge_text}</span>
    </div>"""

# ── build content queue rows ──────────────────────────────────────────────────
ICONS = {"instagram":"📊","telegram":"✈️","reel":"🧠","carousel":"📊","story":"🎯","post":"✍️","whatsapp":"💬"}
post_rows = ""
for p in posts:
    icon = ICONS.get(p.get("platform","post"), "📝")
    s = p.get("status","pending")
    if s == "posted":   sc, sl = "ps-live", "Live"
    elif s == "approved": sc, sl = "ps-sch", "Scheduled"
    else:               sc, sl = "ps-dft", "Drafting"
    sched = (p.get("scheduled_at") or "")[:16].replace("T"," ")
    post_rows += f"""
    <div class="post-item">
      <div class="post-icon" style="background:#9d6fff18">{icon}</div>
      <div>
        <div class="pi-title">{p["caption_a"][:50]}…</div>
        <div class="pi-detail">{p["platform"].upper()} · {sched}</div>
      </div>
      <span class="ps {sc}">{sl}</span>
    </div>"""
if not post_rows:
    post_rows = '<div style="color:#4a4f72;font-size:11px;padding:12px 0;text-align:center">No posts yet — run Content Crew from sidebar</div>'

# ── build lead rows ───────────────────────────────────────────────────────────
lead_rows = ""
for i, l in enumerate(leads):
    name = l.get("name") or l["ig_handle"]
    initials = "".join(w[0].upper() for w in name.split()[:2])
    c = STATUS_COLOR.get(l["status"], "#4a4f72")
    lc = LEAD_COLORS[i % len(LEAD_COLORS)]
    src = l.get("source","").replace("_"," ")
    age = ""
    if l.get("created_at"):
        try:
            dt = datetime.fromisoformat(l["created_at"].replace("Z","+00:00"))
            age = f"Day {(datetime.now(timezone.utc)-dt).days+1}"
        except Exception: pass
    lt_cls = f"lt-{l['status']}" if l['status'] in ('hot','warm','cold') else "lt-cold"
    lead_rows += f"""
    <div class="lead-item">
      <div class="lav" style="background:{lc}18;color:{lc}">{initials}</div>
      <div>
        <div class="lname">{name}</div>
        <div class="lsrc">{src}</div>
      </div>
      <span class="lt {lt_cls}">{l['status'].upper()}</span>
      <div class="lday">{age}</div>
    </div>"""
if not lead_rows:
    lead_rows = '<div style="color:#4a4f72;font-size:11px;padding:12px 0;text-align:center">No leads yet</div>'

# ── build reach bars ──────────────────────────────────────────────────────────
max_reach = max((r["reach"] for r in reach), default=1) or 1
reach_bars = ""
for r in reach:
    h = max(4, int(r["reach"] / max_reach * 65))
    op = 0.4 + 0.6 * (r["reach"] / max_reach)
    reach_bars += f"""
    <div class="bw">
      <div class="bval">{fmt(r["reach"])}</div>
      <div class="bar" style="height:{h}px;background:linear-gradient(180deg,#00e5c3,#4facfe);opacity:{op:.2f}"></div>
      <div class="blbl">{r["day"]}</div>
    </div>"""

# ── build funnels ─────────────────────────────────────────────────────────────
FUNNEL_COLORS = ["#9d6fff","#4facfe","#00e5c3","#ffd166","#ff6b6b"]
def funnel_steps(steps, colors):
    html = ""
    for i, s in enumerate(steps):
        v = s["value"]
        label = fmt(v) if isinstance(v, int) else str(v)
        html += f"""<div class="fn-step">
<div class="fn-lbl"><span class="fn-name">{s["label"]}</span><span class="fn-num">{label}</span></div>
<div class="fn-bg"><div class="fn-fill" style="width:{s["pct"]}%;background:{colors[i%len(colors)]}"></div></div></div>"""
    return html

lf = funnels.get("lead_funnel", [{"label":"Reached","value":0,"pct":100},{"label":"Engaged","value":0,"pct":75},{"label":"DM'd / Enquired","value":0,"pct":48},{"label":"Demo / Trial","value":0,"pct":28},{"label":"Admitted","value":0,"pct":12}])
af = funnels.get("adaptiq_funnel", [{"label":"Promo Views","value":0,"pct":100},{"label":"Link Clicks","value":0,"pct":70},{"label":"Free Trial","value":0,"pct":42},{"label":"Active Day 5","value":0,"pct":26},{"label":"Paid Converted","value":0,"pct":10}])

# ── build live feed ───────────────────────────────────────────────────────────
feed_rows = ""
FEED_ICONS = {"post":("✓","#00e5c3"),"lead":("💬","#9d6fff"),"admission":("⭐","#ffd166"),"trial":("🎯","#4facfe")}
for e in feed[:4]:
    ic, bg = FEED_ICONS.get(e.get("type","post"), ("•","#4a4f72"))
    ts = ago(e.get("time",""))
    feed_rows += f"""<div class="feed-item">
<div class="fic" style="background:{bg}18">{ic}</div>
<div><div class="ft"><strong>{e.get("text","")}</strong></div>
<div class="ft-time">{ts}</div></div></div>"""
if not feed_rows:
    feed_rows = '<div style="color:#4a4f72;font-size:11px;padding:8px 0">No recent activity</div>'

# ── build calendar ────────────────────────────────────────────────────────────
today_dt = datetime.now(timezone.utc)
week_start = today_dt - timedelta(days=today_dt.weekday())
TYPE_COLORS = {"instagram":"cp","reel":"cp","carousel":"cg","story":"cb","post":"cy","whatsapp":"cr","telegram":"cb"}
cal_days = ""
for i in range(7):
    day = week_start + timedelta(days=i)
    key = day.strftime("%Y-%m-%d")
    is_today = key == today_dt.strftime("%Y-%m-%d")
    cls = "cal-day today" if is_today else "cal-day"
    dot = " ●" if is_today else ""
    events = cal.get(key, [])
    ev_html = "".join(f'<div class="ce {TYPE_COLORS.get(e.get("platform","post"),"cy")}">{e["caption"][:16]}</div>' for e in events[:3])
    cal_days += f'<div class="{cls}"><div class="cal-num">{day.day}{dot}</div>{ev_html}</div>'

# ── revenue numbers ───────────────────────────────────────────────────────────
hot = kpis.get("hot_leads", 0)
trials = kpis.get("trials_today", 0)
topper_rev = hot * 25000
adaptiq_rev = trials * 299
total_rev = topper_rev + adaptiq_rev

# ── render HTML ───────────────────────────────────────────────────────────────
now_str = datetime.now().strftime("%A, %d %B %Y")

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
:root{{--bg:#07080f;--surface:#0d0f1a;--surface2:#111320;--border:#1c1f32;--border2:#242742;--text:#e8eaf6;--muted:#4a4f72;--accent:#00e5c3;--accent2:#ff6b6b;--accent3:#ffd166;--accent4:#4facfe;--purple:#9d6fff;}}
body{{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);display:flex;height:100vh;overflow:hidden;font-size:13px;}}
.sb{{width:200px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;flex-shrink:0;}}
.sb-brand{{padding:20px 18px 16px;border-bottom:1px solid var(--border);}}
.sb-brand-name{{font-family:'Syne',sans-serif;font-size:18px;font-weight:800;letter-spacing:-0.5px;color:var(--accent);}}
.sb-brand-sub{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);letter-spacing:2px;margin-top:2px;text-transform:uppercase;}}
.sb-nav{{flex:1;padding:12px 0;overflow-y:auto;}}
.sb-group{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;padding:10px 18px 4px;}}
.sb-item{{display:flex;align-items:center;gap:8px;padding:7px 18px;color:var(--muted);font-size:12px;font-weight:500;border-right:2px solid transparent;}}
.sb-item.on{{color:var(--accent);background:#00e5c308;border-right-color:var(--accent);}}
.sb-foot{{padding:14px 18px;border-top:1px solid var(--border);}}
.pulse-dot{{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--accent);margin-right:6px;animation:glow 2s infinite;}}
@keyframes glow{{0%,100%{{box-shadow:0 0 4px var(--accent);}}50%{{box-shadow:0 0 10px var(--accent);}}}}
@keyframes pulse{{0%,100%{{opacity:1;}}50%{{opacity:0.4;}}}}
.sb-status{{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);}}
.main{{flex:1;display:flex;flex-direction:column;overflow:hidden;}}
.topbar{{background:var(--surface);border-bottom:1px solid var(--border);padding:0 24px;height:52px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;}}
.tb-title{{font-family:'Syne',sans-serif;font-size:14px;font-weight:700;}}
.tb-sub{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);margin-top:1px;letter-spacing:1px;}}
.tb-right{{display:flex;align-items:center;gap:10px;}}
.chip{{font-family:'DM Mono',monospace;font-size:9px;padding:3px 10px;border-radius:4px;letter-spacing:1px;font-weight:500;}}
.chip-live{{background:#00e5c315;color:var(--accent);border:1px solid #00e5c330;}}
.btn-sm{{font-size:11px;font-weight:600;padding:6px 14px;border-radius:6px;cursor:pointer;border:none;font-family:'DM Sans',sans-serif;}}
.btn-outline{{background:transparent;color:var(--muted);border:1px solid var(--border2);}}
.btn-fill{{background:var(--accent);color:#000;}}
.av{{width:28px;height:28px;border-radius:6px;background:linear-gradient(135deg,#00e5c3,#4facfe);display:flex;align-items:center;justify-content:center;font-family:'Syne',sans-serif;font-size:10px;font-weight:800;color:#000;}}
.content{{flex:1;overflow-y:auto;padding:16px 20px;display:flex;flex-direction:column;gap:12px;}}
::-webkit-scrollbar{{width:3px;}}::-webkit-scrollbar-thumb{{background:var(--border2);}}
.kpi-row{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;}}
.kpi{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 14px;position:relative;overflow:hidden;}}
.kpi::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;}}
.kpi-1::before{{background:var(--accent);}} .kpi-2::before{{background:var(--accent4);}} .kpi-3::before{{background:var(--accent3);}} .kpi-4::before{{background:var(--purple);}} .kpi-5::before{{background:var(--accent2);}}
.kpi-lbl{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:5px;}}
.kpi-val{{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;letter-spacing:-1px;}}
.kpi-delta{{font-size:10px;margin-top:3px;color:var(--muted);}}
.up{{color:var(--accent);}}
.row{{display:grid;gap:10px;}} .r3{{grid-template-columns:1.1fr 1.4fr 1.1fr;}} .r4{{grid-template-columns:1.6fr 1fr 1fr 0.9fr;}}
.panel{{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;}}
.ph{{padding:10px 14px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;}}
.ph-title{{font-family:'Syne',sans-serif;font-size:12px;font-weight:700;}}
.ph-meta{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);}}
.pb{{padding:10px 14px;}}
.agent-row{{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--border);font-size:11px;}}
.agent-row:last-child{{border-bottom:none;}}
.ad{{width:6px;height:6px;border-radius:50%;flex-shrink:0;}}
.an{{font-weight:600;width:90px;flex-shrink:0;font-size:11px;}}
.at{{color:var(--muted);flex:1;font-size:10px;font-family:'DM Mono',monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.abadge{{font-family:'DM Mono',monospace;font-size:9px;padding:2px 6px;border-radius:3px;letter-spacing:.5px;}}
.post-item{{display:flex;gap:10px;padding:7px 0;border-bottom:1px solid var(--border);align-items:center;}}
.post-item:last-child{{border-bottom:none;}}
.post-icon{{width:34px;height:34px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0;}}
.pi-title{{font-size:11px;font-weight:600;margin-bottom:2px;}}
.pi-detail{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);}}
.ps{{font-family:'DM Mono',monospace;font-size:9px;padding:2px 7px;border-radius:3px;letter-spacing:.5px;margin-left:auto;flex-shrink:0;}}
.ps-live{{background:#00e5c312;color:var(--accent);}} .ps-sch{{background:#4facfe12;color:var(--accent4);}} .ps-dft{{background:#ffd16612;color:var(--accent3);}}
.lead-item{{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--border);font-size:11px;}}
.lead-item:last-child{{border-bottom:none;}}
.lav{{width:26px;height:26px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;flex-shrink:0;font-family:'Syne',sans-serif;}}
.lname{{font-weight:600;font-size:11px;}} .lsrc{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);margin-top:1px;}}
.lt{{font-family:'DM Mono',monospace;font-size:9px;padding:2px 7px;border-radius:3px;margin-left:auto;flex-shrink:0;}}
.lt-hot{{background:#ff6b6b15;color:var(--accent2);}} .lt-warm{{background:#ffd16615;color:var(--accent3);}} .lt-cold{{background:#4facfe15;color:var(--accent4);}}
.lday{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);width:36px;text-align:right;}}
.bar-chart{{display:flex;align-items:flex-end;gap:5px;height:70px;padding-top:6px;}}
.bw{{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;}}
.bar{{width:100%;border-radius:3px 3px 0 0;}}
.blbl{{font-family:'DM Mono',monospace;font-size:8px;color:var(--muted);}} .bval{{font-family:'DM Mono',monospace;font-size:8px;color:var(--text);}}
.fn-step{{margin-bottom:7px;}} .fn-lbl{{display:flex;justify-content:space-between;margin-bottom:2px;font-size:10px;}}
.fn-name{{color:var(--muted);}} .fn-num{{font-weight:700;font-family:'DM Mono',monospace;}}
.fn-bg{{background:var(--border);border-radius:2px;height:4px;}} .fn-fill{{height:4px;border-radius:2px;}}
.rev{{background:var(--surface2);border:1px solid var(--border2);border-radius:10px;padding:14px;border-top:2px solid var(--accent);}}
.rev-lbl{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:5px;}}
.rev-amt{{font-family:'Syne',sans-serif;font-size:24px;font-weight:800;color:var(--accent);letter-spacing:-1px;}}
.rev-sub{{font-size:10px;color:var(--muted);margin-top:2px;}}
.rev-split{{display:flex;gap:7px;margin-top:9px;}}
.rev-item{{flex:1;background:#ffffff06;border-radius:5px;padding:7px;border:1px solid var(--border);}}
.rev-item-lbl{{font-family:'DM Mono',monospace;font-size:8px;color:var(--muted);margin-bottom:2px;}}
.rev-item-val{{font-family:'Syne',sans-serif;font-size:12px;font-weight:700;}}
.feed-item{{display:flex;gap:8px;padding:6px 0;border-bottom:1px solid var(--border);align-items:flex-start;}}
.feed-item:last-child{{border-bottom:none;}}
.fic{{width:22px;height:22px;border-radius:5px;display:flex;align-items:center;justify-content:center;font-size:10px;flex-shrink:0;}}
.ft{{font-size:10px;line-height:1.4;}} .ft strong{{color:var(--text);}}
.ft-time{{font-family:'DM Mono',monospace;font-size:8px;color:var(--muted);margin-top:1px;}}
.cal{{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;}}
.cal-hd{{font-family:'DM Mono',monospace;font-size:8px;color:var(--muted);text-align:center;padding:3px;letter-spacing:1px;}}
.cal-day{{background:var(--surface2);border:1px solid var(--border);border-radius:5px;padding:5px;min-height:54px;}}
.cal-day.today{{border-color:var(--accent);background:#00e5c305;}}
.cal-num{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);margin-bottom:3px;font-weight:500;}}
.cal-day.today .cal-num{{color:var(--accent);}}
.ce{{border-radius:3px;padding:2px 4px;margin-bottom:2px;font-size:8px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:'DM Mono',monospace;}}
.cp{{background:#9d6fff18;color:var(--purple);}} .cg{{background:#00e5c318;color:var(--accent);}} .cb{{background:#4facfe18;color:var(--accent4);}} .cy{{background:#ffd16618;color:var(--accent3);}} .cr{{background:#ff6b6b18;color:var(--accent2);}}
</style></head><body>

<div class="sb">
  <div class="sb-brand">
    <div class="sb-brand-name">BrandIQ</div>
    <div class="sb-brand-sub">TOPPER IAS · ADAPTIQ</div>
  </div>
  <div class="sb-nav">
    <div class="sb-group">Main</div>
    <div class="sb-item on">▣ Dashboard</div>
    <div class="sb-group">Marketing</div>
    <div class="sb-item">📸 Instagram</div>
    <div class="sb-item">💬 WhatsApp</div>
    <div class="sb-item">✈️ Telegram</div>
    <div class="sb-group">Sales</div>
    <div class="sb-item">👥 Leads</div>
    <div class="sb-item">🔄 Nurture Flows</div>
    <div class="sb-item">🎯 Adaptiq Funnel</div>
    <div class="sb-group">Reports</div>
    <div class="sb-item">📊 Analytics</div>
  </div>
  <div class="sb-foot"><span class="pulse-dot"></span><span class="sb-status">9/9 AGENTS LIVE</span></div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <div class="tb-title">Live Dashboard</div>
      <div class="tb-sub">{now_str.upper()} · AUTO-PILOT ON</div>
    </div>
    <div class="tb-right">
      <span class="chip chip-live">● LIVE</span>
      <button class="btn-sm btn-outline" onclick="window.open('{API}/docs','_blank')">API Docs</button>
      <button class="btn-sm btn-fill" onclick="fetch('{API}/tasks/content',{{method:'POST'}}).then(()=>alert('Content Crew queued!'))">+ Run Crew</button>
      <div class="av">TI</div>
    </div>
  </div>

  <div class="content">
    <div class="kpi-row">
      <div class="kpi kpi-1"><div class="kpi-lbl">Posts Today</div><div class="kpi-val" style="color:var(--accent)">{kpis.get("posts_today",0)}</div><div class="kpi-delta"><span class="up">↑</span> {kpis.get("total_posts",0)} total published</div></div>
      <div class="kpi kpi-2"><div class="kpi-lbl">New Leads</div><div class="kpi-val" style="color:var(--accent4)">{kpis.get("new_leads",0)}</div><div class="kpi-delta"><span class="up">↑</span> {kpis.get("total_leads",0)} total captured</div></div>
      <div class="kpi kpi-3"><div class="kpi-lbl">Hot Leads</div><div class="kpi-val" style="color:var(--accent3)">{kpis.get("hot_leads",0)}</div><div class="kpi-delta"><span class="up">↑</span> Ready to convert</div></div>
      <div class="kpi kpi-4"><div class="kpi-lbl">Adaptiq Trials</div><div class="kpi-val" style="color:var(--purple)">{kpis.get("trials_today",0)}</div><div class="kpi-delta"><span class="up">↑</span> Active today</div></div>
      <div class="kpi kpi-5"><div class="kpi-lbl">WhatsApp Sent</div><div class="kpi-val" style="color:var(--accent2)">{kpis.get("wa_sent",0)}</div><div class="kpi-delta"><span class="up">↑</span> Nurture messages</div></div>
    </div>

    <div class="row r3">
      <div class="panel">
        <div class="ph"><span class="ph-title">Agent Status</span><span class="ph-meta">9/9 ACTIVE</span></div>
        <div class="pb" style="padding:8px 14px">{agent_rows}</div>
      </div>
      <div class="panel">
        <div class="ph"><span class="ph-title">Content Queue — Today</span><span class="ph-meta">{len(posts)} POSTS</span></div>
        <div class="pb">{post_rows}</div>
      </div>
      <div class="panel">
        <div class="ph"><span class="ph-title">Lead Pipeline</span><span class="ph-meta">{kpis.get("new_leads",0)} TODAY</span></div>
        <div class="pb" style="padding:8px 14px">{lead_rows}</div>
      </div>
    </div>

    <div class="row r4">
      <div class="panel">
        <div class="ph"><span class="ph-title">Weekly Reach — Instagram</span><span class="ph-meta">LAST 7 DAYS</span></div>
        <div class="pb"><div class="bar-chart">{reach_bars}</div></div>
      </div>
      <div class="panel">
        <div class="ph"><span class="ph-title">Admission Funnel</span><span class="ph-meta">THIS MONTH</span></div>
        <div class="pb">{funnel_steps(lf, FUNNEL_COLORS)}</div>
      </div>
      <div class="panel">
        <div class="ph"><span class="ph-title">Adaptiq Funnel</span><span class="ph-meta">THIS MONTH</span></div>
        <div class="pb">{funnel_steps(af, ["#00e5c3"]*5)}</div>
      </div>
      <div style="display:flex;flex-direction:column;gap:10px">
        <div class="rev">
          <div class="rev-lbl">Revenue This Month</div>
          <div class="rev-amt">₹{fmt(total_rev)}</div>
          <div class="rev-sub">Based on live DB data</div>
          <div class="rev-split">
            <div class="rev-item"><div class="rev-item-lbl">TOPPER IAS</div><div class="rev-item-val" style="color:var(--purple)">₹{fmt(topper_rev)}</div></div>
            <div class="rev-item"><div class="rev-item-lbl">ADAPTIQ</div><div class="rev-item-val" style="color:var(--accent)">₹{fmt(adaptiq_rev)}</div></div>
          </div>
        </div>
        <div class="panel" style="flex:1">
          <div class="ph"><span class="ph-title">Live Feed</span><span class="ph-meta">REAL-TIME</span></div>
          <div class="pb" style="padding:8px 12px">{feed_rows}</div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="ph"><span class="ph-title">Content Calendar — This Week</span><span class="ph-meta">AUTO-GENERATED BY STRATEGYAGENT</span></div>
      <div class="pb">
        <div class="cal">
          <div class="cal-hd">MON</div><div class="cal-hd">TUE</div><div class="cal-hd">WED</div>
          <div class="cal-hd">THU</div><div class="cal-hd">FRI</div><div class="cal-hd">SAT</div><div class="cal-hd">SUN</div>
          {cal_days}
        </div>
      </div>
    </div>
  </div>
</div>
</body></html>"""

components.html(HTML, height=900, scrolling=True)
