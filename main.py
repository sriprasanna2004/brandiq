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
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
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
