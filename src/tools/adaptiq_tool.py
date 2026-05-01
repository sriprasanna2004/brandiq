import uuid
from datetime import datetime, timezone, timedelta

from loguru import logger
from sqlalchemy import select

from src.database import AsyncSessionLocal
from src.models import AgentJob, JobStatus, AdaptiqTrial, Lead, LeadStatus


async def start_trial(lead_id: str, lead_phone: str, lead_name: str) -> bool:
    from src.tools.whatsapp_tool import send_text_message
    from src.agents.adaptiq_promo_agent import run_adaptiq_promo_agent

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        trial = AdaptiqTrial(
            id=uuid.uuid4(),
            lead_id=uuid.UUID(lead_id),
            trial_start=now,
            trial_end=now + timedelta(days=7),
        )
        db.add(trial)
        await db.commit()

    try:
        msg = run_adaptiq_promo_agent(lead_name=lead_name, trial_day=1, weak_subjects=[])
        await send_text_message(phone=lead_phone, message=msg.message)
        logger.info(f"[Adaptiq] Trial started for lead_id={lead_id}, Day 1 message sent to {lead_phone}")
        return True
    except Exception as e:
        logger.error(f"[Adaptiq] start_trial failed for lead_id={lead_id}: {e}")
        return False


async def run_trial_sequences() -> int:
    from src.tools.whatsapp_tool import send_text_message
    from src.agents.adaptiq_promo_agent import run_adaptiq_promo_agent

    now = datetime.now(timezone.utc)
    sent_count = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AdaptiqTrial).where(
                AdaptiqTrial.converted_at.is_(None),
                AdaptiqTrial.trial_end >= now,
            )
        )
        trials = result.scalars().all()
        logger.info(f"[Adaptiq] Processing {len(trials)} active trial(s)")

        for trial in trials:
            trial_day = (now - trial.trial_start).days
            if trial_day not in (1, 3, 5, 7):
                continue

            lead = await db.scalar(select(Lead).where(Lead.id == trial.lead_id))
            if not lead or not lead.phone:
                continue

            job_id = f"adaptiq_{lead.id}_{trial_day}"
            already = await db.scalar(select(AgentJob).where(AgentJob.job_id == job_id))
            if already:
                continue

            job = AgentJob(
                id=uuid.uuid4(),
                job_id=job_id,
                agent_name="AdaptiqPromoAgent",
                status=JobStatus.running,
                payload={"lead_id": str(lead.id), "trial_day": trial_day},
            )
            db.add(job)
            await db.commit()

            try:
                msg = run_adaptiq_promo_agent(
                    lead_name=lead.name or lead.ig_handle,
                    trial_day=trial_day,
                    weak_subjects=[],
                )
                await send_text_message(phone=lead.phone, message=msg.message)
                job.status = JobStatus.success
                job.completed_at = now
                sent_count += 1
                logger.info(f"[Adaptiq] Day {trial_day} message sent to {lead.phone}")
            except Exception as e:
                job.status = JobStatus.failed
                job.error = str(e)
                job.completed_at = now
                logger.error(f"[Adaptiq] Day {trial_day} failed for lead {lead.id}: {e}")

            await db.commit()

    return sent_count


async def mark_converted(lead_id: str, plan: str) -> bool:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        trial = await db.scalar(
            select(AdaptiqTrial).where(AdaptiqTrial.lead_id == uuid.UUID(lead_id))
        )
        if trial:
            trial.converted_at = now
            trial.plan = plan

        lead = await db.scalar(select(Lead).where(Lead.id == uuid.UUID(lead_id)))
        if lead:
            lead.status = LeadStatus.hot
            lead.updated_at = now

        await db.commit()

    logger.info(f"[Adaptiq] Conversion recorded for lead_id={lead_id}, plan={plan}")
    return True
