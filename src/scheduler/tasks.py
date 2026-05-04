import asyncio
import os
from datetime import date

import sentry_sdk
from celery import Celery
from loguru import logger

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# Railway Redis uses rediss:// — append ssl_cert_reqs=none to URL
if REDIS_URL.startswith("rediss://") and "ssl_cert_reqs" not in REDIS_URL:
    REDIS_URL_BROKER = REDIS_URL + ("&" if "?" in REDIS_URL else "?") + "ssl_cert_reqs=none"
else:
    REDIS_URL_BROKER = REDIS_URL

celery_app = Celery(
    "brandiq",
    broker=REDIS_URL_BROKER,
    backend=REDIS_URL_BROKER,
    include=["src.scheduler.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
)


def _send_telegram_alert(message: str) -> None:
    """Fire-and-forget Telegram alert to admin (sync wrapper for Celery context)."""
    try:
        import httpx
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
        if not token or not chat_id:
            return
        httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
    except Exception as e:
        logger.warning(f"Telegram alert failed: {e}")


# ---------------------------------------------------------------------------
# Task 1: Content crew
# ---------------------------------------------------------------------------

@celery_app.task(
    name="content.weekly",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def run_content_crew_task(self):
    from src.crews.content_crew import run_content_crew
    try:
        result = asyncio.run(run_content_crew(week_start=date.today()))
        logger.info("Content crew completed successfully")
        return result
    except Exception as exc:
        logger.error(f"[content.weekly] Attempt {self.request.retries + 1} failed: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            msg = f"[BrandIQ] Content crew failed after 3 retries: {exc}"
            logger.error(msg)
            sentry_sdk.capture_exception(exc)
            _send_telegram_alert(msg)
            try:
                from src.tools.telegram_tool import send_failure_alert
                asyncio.run(send_failure_alert(
                    agent_name="ContentCrew",
                    error=str(exc),
                    job_id=f"content_{date.today()}",
                ))
            except Exception:
                pass
            raise


# ---------------------------------------------------------------------------
# Task 2: Lead crew
# ---------------------------------------------------------------------------

@celery_app.task(
    name="lead.process",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def run_lead_crew_task(self, ig_handle: str, message_text: str = "", day_number: int = 0):
    from src.crews.lead_crew import run_lead_crew
    try:
        result = asyncio.run(run_lead_crew(
            ig_handle=ig_handle,
            message_text=message_text,
            day_number=day_number,
        ))
        return result
    except Exception as exc:
        logger.error(f"[lead.process] @{ig_handle} day={day_number} failed: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            sentry_sdk.capture_exception(exc)
            try:
                from src.tools.telegram_tool import send_failure_alert
                asyncio.run(send_failure_alert(
                    agent_name="LeadCrew",
                    error=str(exc),
                    job_id=f"lead_{ig_handle}_{day_number}",
                ))
            except Exception:
                pass
            raise


# ---------------------------------------------------------------------------
# Task 3: Analytics crew
# ---------------------------------------------------------------------------

@celery_app.task(
    name="analytics.daily",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def run_analytics_crew_task(self):
    from src.crews.analytics_crew import run_analytics_crew
    try:
        result = asyncio.run(run_analytics_crew())
        return result
    except Exception as exc:
        logger.error(f"[analytics.daily] Failed: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            sentry_sdk.capture_exception(exc)
            try:
                from src.tools.telegram_tool import send_failure_alert
                asyncio.run(send_failure_alert(
                    agent_name="AnalyticsCrew",
                    error=str(exc),
                    job_id=f"analytics_{date.today()}",
                ))
            except Exception:
                pass
            raise
