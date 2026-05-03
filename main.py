import os
import asyncio
import subprocess
from datetime import date, datetime, timezone

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class LeadTaskRequest(BaseModel):
    ig_handle: str
    message_text: str = "what are the fees for batch?"
    day_number: int = 0

class ApprovePostRequest(BaseModel):
    post_id: str

# ---------------------------------------------------------------------------
# Sentry
# ---------------------------------------------------------------------------
sentry_dsn = os.getenv("SENTRY_DSN", "")
if sentry_dsn and sentry_dsn != "REPLACE_ME":
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.getenv("ENVIRONMENT", "development"),
        traces_sample_rate=0.2,
    )

# ---------------------------------------------------------------------------
# Loguru
# ---------------------------------------------------------------------------
log_level = os.getenv("LOG_LEVEL", "INFO")
logger.remove()
logger.add(
    sink=lambda msg: print(msg, end=""),
    level=log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    colorize=True,
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="BrandIQ", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    logger.info("Running alembic upgrade head...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f"Alembic migration failed:\n{result.stderr}")
    else:
        logger.info("Migrations applied successfully.")

    from src.scheduler.cron_jobs import start_scheduler
    start_scheduler()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# ---------------------------------------------------------------------------
# Manual task triggers
# ---------------------------------------------------------------------------

@app.post("/tasks/content")
async def trigger_content_crew():
    from src.scheduler.tasks import run_content_crew_task
    task = run_content_crew_task.delay()
    logger.info(f"[API] Content crew triggered, task_id={task.id}")
    return {"task_id": task.id, "status": "queued"}


@app.post("/tasks/analytics")
async def trigger_analytics_crew():
    from src.scheduler.tasks import run_analytics_crew_task
    task = run_analytics_crew_task.delay()
    logger.info(f"[API] Analytics crew triggered, task_id={task.id}")
    return {"task_id": task.id, "status": "queued"}


@app.post("/tasks/lead")
async def trigger_lead_crew(body: LeadTaskRequest):
    from src.scheduler.tasks import run_lead_crew_task
    task = run_lead_crew_task.delay(
        ig_handle=body.ig_handle,
        message_text=body.message_text,
        day_number=body.day_number,
    )
    return {"task_id": task.id, "status": "queued", "ig_handle": body.ig_handle, "day_number": body.day_number}


@app.get("/posts")
async def list_posts(status: str = None, limit: int = 20):
    from sqlalchemy import select
    from src.database import AsyncSessionLocal
    from src.models import Post, PostStatus
    async with AsyncSessionLocal() as db:
        q = select(Post).order_by(Post.scheduled_at.desc()).limit(limit)
        if status:
            q = q.where(Post.status == PostStatus(status))
        result = await db.execute(q)
        posts = result.scalars().all()
        return [
            {
                "id": str(p.id), "platform": p.platform.value,
                "caption_a": p.caption_a[:80], "status": p.status.value,
                "scheduled_at": p.scheduled_at.isoformat() if p.scheduled_at else None,
                "posted_at": p.posted_at.isoformat() if p.posted_at else None,
            }
            for p in posts
        ]


@app.post("/posts/approve")
async def approve_post(body: ApprovePostRequest):
    from sqlalchemy import select
    from src.database import AsyncSessionLocal
    from src.models import Post, PostStatus
    import uuid
    async with AsyncSessionLocal() as db:
        post = await db.scalar(select(Post).where(Post.id == uuid.UUID(body.post_id)))
        if not post:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Post not found")
        post.status = PostStatus.approved
        await db.commit()
        return {"post_id": body.post_id, "status": "approved"}


@app.post("/posts/publish/{post_id}")
async def publish_post_now(post_id: str):
    from src.tools.post_publisher import publish_single_post
    success = await publish_single_post(post_id)
    return {"post_id": post_id, "published": success}


@app.get("/leads")
async def list_leads(status: str = None, limit: int = 50):
    from sqlalchemy import select
    from src.database import AsyncSessionLocal
    from src.models import Lead, LeadStatus
    async with AsyncSessionLocal() as db:
        q = select(Lead).order_by(Lead.created_at.desc()).limit(limit)
        if status:
            q = q.where(Lead.status == LeadStatus(status))
        result = await db.execute(q)
        leads = result.scalars().all()
        return [
            {
                "id": str(l.id), "ig_handle": l.ig_handle, "name": l.name,
                "phone": l.phone, "status": l.status.value, "source": l.source.value,
                "created_at": l.created_at.isoformat(),
            }
            for l in leads
        ]


@app.get("/stats/kpis")
async def get_kpis():
    from sqlalchemy import select, func
    from src.database import AsyncSessionLocal
    from src.models import Post, PostStatus, Lead, LeadStatus, WhatsappSequence, SequenceStatus, AdaptiqTrial
    from datetime import timezone
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    async with AsyncSessionLocal() as db:
        posts_today   = await db.scalar(select(func.count(Post.id)).where(Post.posted_at >= today, Post.status == PostStatus.posted)) or 0
        new_leads     = await db.scalar(select(func.count(Lead.id)).where(Lead.created_at >= today)) or 0
        hot_leads     = await db.scalar(select(func.count(Lead.id)).where(Lead.status == LeadStatus.hot, Lead.created_at >= today)) or 0
        wa_sent       = await db.scalar(select(func.count(WhatsappSequence.id)).where(WhatsappSequence.sent_at >= today, WhatsappSequence.status == SequenceStatus.sent)) or 0
        trials        = await db.scalar(select(func.count(AdaptiqTrial.id)).where(AdaptiqTrial.trial_start >= today)) or 0
        total_leads   = await db.scalar(select(func.count(Lead.id))) or 0
        total_posts   = await db.scalar(select(func.count(Post.id)).where(Post.status == PostStatus.posted)) or 0
    return {
        "posts_today": posts_today, "new_leads": new_leads, "hot_leads": hot_leads,
        "wa_sent": wa_sent, "trials_today": trials,
        "total_leads": total_leads, "total_posts": total_posts,
    }


@app.get("/stats/agent-status")
async def get_agent_status():
    from sqlalchemy import select
    from src.database import AsyncSessionLocal
    from src.models import AgentJob
    from datetime import timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    agents = [
        "ContentCrew","LeadCrew","AnalyticsCrew",
        "StrategyAgent","ContentWriterAgent","VisualCreatorAgent",
        "SchedulerAgent","LeadCaptureAgent","LeadNurtureAgent",
        "ReelScriptAgent","AnalyticsAgent","AdaptiqPromoAgent",
    ]
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AgentJob)
            .where(AgentJob.created_at >= cutoff)
            .order_by(AgentJob.created_at.desc())
        )
        jobs = result.scalars().all()
    latest = {}
    for j in jobs:
        if j.agent_name not in latest:
            latest[j.agent_name] = {"agent_name": j.agent_name, "status": j.status.value, "job_id": j.job_id, "created_at": j.created_at.isoformat()}
    return list(latest.values())


@app.get("/stats/live-feed")
async def get_live_feed():
    from sqlalchemy import select, or_
    from src.database import AsyncSessionLocal
    from src.models import AgentJob, Lead, LeadStatus, Post, PostStatus
    from datetime import timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=12)
    events = []
    async with AsyncSessionLocal() as db:
        posts = await db.execute(select(Post).where(Post.posted_at >= cutoff, Post.status == PostStatus.posted).order_by(Post.posted_at.desc()).limit(5))
        for p in posts.scalars().all():
            events.append({"type": "post", "icon": "✓", "text": f"Post published — \"{p.caption_a[:40]}...\"", "time": p.posted_at.isoformat(), "color": "#00e5c3"})
        leads = await db.execute(select(Lead).where(Lead.created_at >= cutoff, Lead.status == LeadStatus.hot).order_by(Lead.created_at.desc()).limit(5))
        for l in leads.scalars().all():
            events.append({"type": "lead", "icon": "💬", "text": f"Hot lead — @{l.ig_handle}", "time": l.created_at.isoformat(), "color": "#9d6fff"})
    events.sort(key=lambda x: x["time"], reverse=True)
    return events[:8]


@app.get("/stats/reach")
async def get_reach():
    from sqlalchemy import select, func
    from src.database import AsyncSessionLocal
    from src.models import PostAnalytics
    from datetime import timezone, timedelta
    async with AsyncSessionLocal() as db:
        rows = []
        for i in range(6, -1, -1):
            day = datetime.now(timezone.utc) - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59)
            reach = await db.scalar(select(func.sum(PostAnalytics.reach)).where(PostAnalytics.recorded_at >= day_start, PostAnalytics.recorded_at <= day_end)) or 0
            rows.append({"day": day.strftime("%a"), "reach": reach})
    return rows


@app.get("/stats/funnels")
async def get_funnels():
    from sqlalchemy import select, func
    from src.database import AsyncSessionLocal
    from src.models import Lead, LeadStatus, AdaptiqTrial, PostAnalytics
    from datetime import timezone
    today = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    async with AsyncSessionLocal() as db:
        total_leads = await db.scalar(select(func.count(Lead.id)).where(Lead.created_at >= today)) or 0
        hot_leads = await db.scalar(select(func.count(Lead.id)).where(Lead.status == LeadStatus.hot, Lead.created_at >= today)) or 0
        trials = await db.scalar(select(func.count(AdaptiqTrial.id)).where(AdaptiqTrial.trial_start >= today)) or 0
        converted = await db.scalar(select(func.count(AdaptiqTrial.id)).where(AdaptiqTrial.converted_at.isnot(None), AdaptiqTrial.trial_start >= today)) or 0
        total_reach = await db.scalar(select(func.sum(PostAnalytics.reach)).where(PostAnalytics.recorded_at >= today)) or 0
    return {
        "lead_funnel": [
            {"label": "Reached", "value": total_reach or 0, "pct": 100},
            {"label": "Engaged", "value": int(total_reach * 0.03) if total_reach else 0, "pct": 75},
            {"label": "Enquired", "value": total_leads, "pct": 48},
            {"label": "Trial", "value": trials, "pct": 28},
            {"label": "Admitted", "value": hot_leads, "pct": 12},
        ],
        "adaptiq_funnel": [
            {"label": "Promo Views", "value": total_reach or 0, "pct": 100},
            {"label": "Link Clicks", "value": int(total_reach * 0.004) if total_reach else 0, "pct": 70},
            {"label": "Free Trial", "value": trials, "pct": 42},
            {"label": "Day 5 Active", "value": int(trials * 0.63) if trials else 0, "pct": 26},
            {"label": "Converted", "value": converted, "pct": 10},
        ],
    }


@app.get("/calendar")
async def get_calendar():
    from sqlalchemy import select
    from src.database import AsyncSessionLocal
    from src.models import Post
    from datetime import timezone, timedelta
    today = datetime.now(timezone.utc)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Post).where(Post.scheduled_at >= week_start, Post.scheduled_at <= week_end).order_by(Post.scheduled_at))
        posts = result.scalars().all()
    calendar = {}
    for p in posts:
        day = p.scheduled_at.strftime("%Y-%m-%d")
        if day not in calendar:
            calendar[day] = []
        calendar[day].append({"caption": p.caption_a[:30], "platform": p.platform.value, "status": p.status.value})
    return calendar


@app.get("/stats/agent-jobs")
async def get_agent_jobs(limit: int = 20):
    from sqlalchemy import select
    from src.database import AsyncSessionLocal
    from src.models import AgentJob
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AgentJob).order_by(AgentJob.created_at.desc()).limit(limit))
        jobs = result.scalars().all()
        return [
            {
                "job_id": j.job_id, "agent_name": j.agent_name, "status": j.status.value,
                "created_at": j.created_at.isoformat(),
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                "error": j.error,
            }
            for j in jobs
        ]


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

@app.get("/webhook/instagram")
async def instagram_webhook_verify(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
):
    from src.tools.webhook_handler import verify_webhook
    from fastapi import Query
    from fastapi.responses import PlainTextResponse
    challenge = verify_webhook(
        mode=hub_mode or "",
        token=hub_verify_token or "",
        challenge=hub_challenge or "",
    )
    if challenge:
        return PlainTextResponse(challenge)
    from fastapi import HTTPException
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook/instagram")
async def instagram_webhook(request: Request):
    from src.tools.webhook_handler import handle_instagram_event
    payload = await request.json()
    result = await handle_instagram_event(payload)
    return JSONResponse(status_code=200, content=result)
