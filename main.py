import os
import asyncio
import subprocess
from datetime import date, datetime, timezone

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

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
async def trigger_lead_crew(request: Request):
    body = await request.json()
    from src.scheduler.tasks import run_lead_crew_task
    task = run_lead_crew_task.delay(
        ig_handle=body.get("ig_handle", ""),
        message_text=body.get("message_text", ""),
        day_number=body.get("day_number", 0),
    )
    return {"task_id": task.id, "status": "queued"}


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
async def approve_post(request: Request):
    body = await request.json()
    from sqlalchemy import select
    from src.database import AsyncSessionLocal
    from src.models import Post, PostStatus
    import uuid
    async with AsyncSessionLocal() as db:
        post = await db.scalar(select(Post).where(Post.id == uuid.UUID(body["post_id"])))
        if not post:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Post not found")
        post.status = PostStatus.approved
        await db.commit()
        return {"post_id": body["post_id"], "status": "approved"}


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
    from src.models import Post, PostStatus, Lead, WhatsappSequence, SequenceStatus, AdaptiqTrial
    from datetime import timezone
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    async with AsyncSessionLocal() as db:
        posts_today   = await db.scalar(select(func.count(Post.id)).where(Post.posted_at >= today, Post.status == PostStatus.posted)) or 0
        new_leads     = await db.scalar(select(func.count(Lead.id)).where(Lead.created_at >= today)) or 0
        hot_leads     = await db.scalar(select(func.count(Lead.id)).where(Lead.status == "hot", Lead.created_at >= today)) or 0
        wa_sent       = await db.scalar(select(func.count(WhatsappSequence.id)).where(WhatsappSequence.sent_at >= today, WhatsappSequence.status == SequenceStatus.sent)) or 0
        trials        = await db.scalar(select(func.count(AdaptiqTrial.id)).where(AdaptiqTrial.trial_start >= today)) or 0
        total_leads   = await db.scalar(select(func.count(Lead.id))) or 0
        total_posts   = await db.scalar(select(func.count(Post.id)).where(Post.status == PostStatus.posted)) or 0
    return {
        "posts_today": posts_today, "new_leads": new_leads, "hot_leads": hot_leads,
        "wa_sent": wa_sent, "trials_today": trials,
        "total_leads": total_leads, "total_posts": total_posts,
    }


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
