import uuid
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select

from src.database import AsyncSessionLocal
from src.models import AgentJob, JobStatus, Lead, LeadStatus, LeadSource, WhatsappSequence, SequenceStatus
from src.agents.lead_capture_agent import run_lead_capture_agent
from src.agents.lead_nurture_agent import run_lead_nurture_agent


async def run_lead_crew(
    ig_handle: str,
    message_text: str = "",
    day_number: int = 0,
) -> dict:
    job_id = f"lead_{ig_handle}_{day_number}"
    logger.info(f"[LeadCrew] Starting job_id={job_id}")

    async with AsyncSessionLocal() as db:
        existing_job = await db.scalar(select(AgentJob).where(AgentJob.job_id == job_id))
        if existing_job:
            job = existing_job
            job.status = JobStatus.running
        else:
            job = AgentJob(
                id=uuid.uuid4(),
                job_id=job_id,
                agent_name="LeadCrew",
                status=JobStatus.running,
                payload={"ig_handle": ig_handle, "day_number": day_number},
            )
            db.add(job)
        await db.commit()

        try:
            # ----------------------------------------------------------------
            # Day 0: score the lead from an incoming DM
            # ----------------------------------------------------------------
            if day_number == 0:
                logger.info(f"[LeadCrew] Scoring lead @{ig_handle}")
                score = run_lead_capture_agent(message_text=message_text, ig_handle=ig_handle)

                # Upsert lead
                lead = await db.scalar(select(Lead).where(Lead.ig_handle == ig_handle))
                if lead:
                    lead.status = LeadStatus(score.status.value)
                    lead.updated_at = datetime.now(timezone.utc)
                else:
                    lead = Lead(
                        id=uuid.uuid4(),
                        ig_handle=ig_handle,
                        status=LeadStatus(score.status.value),
                        source=LeadSource.instagram_dm,
                    )
                    db.add(lead)

                job.status = JobStatus.success
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()

                logger.info(f"[LeadCrew] Lead @{ig_handle} saved, status={score.status}")
                return score.model_dump()

            # ----------------------------------------------------------------
            # Day 1/3/7/14: nurture sequence
            # ----------------------------------------------------------------
            if day_number not in (1, 3, 7, 14):
                raise ValueError(f"day_number must be 0, 1, 3, 7, or 14 — got {day_number}")

            lead = await db.scalar(select(Lead).where(Lead.ig_handle == ig_handle))
            if not lead:
                raise ValueError(f"Lead @{ig_handle} not found — run day_number=0 first")

            # Idempotency: skip if already sent
            already_sent = await db.scalar(
                select(WhatsappSequence).where(
                    WhatsappSequence.lead_id == lead.id,
                    WhatsappSequence.day_number == day_number,
                )
            )
            if already_sent:
                logger.warning(f"[LeadCrew] Day {day_number} already sent for @{ig_handle}, skipping")
                job.status = JobStatus.success
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()
                return {"skipped": True, "reason": "already_sent", "ig_handle": ig_handle, "day_number": day_number}

            logger.info(f"[LeadCrew] Nurturing @{ig_handle} day={day_number}")
            nurture = run_lead_nurture_agent(
                lead_name=lead.name or ig_handle,
                day_number=day_number,
                lead_status=lead.status.value,
            )

            # Record sequence
            seq = WhatsappSequence(
                id=uuid.uuid4(),
                lead_id=lead.id,
                day_number=day_number,
                template_name=nurture.template_name,
                status=SequenceStatus.sent,
            )
            db.add(seq)

            job.status = JobStatus.success
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(f"[LeadCrew] Nurture message sent, template={nurture.template_name}")
            return nurture.model_dump()

        except Exception as e:
            logger.error(f"[LeadCrew] Failed job_id={job_id}: {e}")
            job.status = JobStatus.failed
            job.error = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()
            raise
