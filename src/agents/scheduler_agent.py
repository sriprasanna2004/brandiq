import os
import json
from datetime import datetime
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger


class ScheduleDecision(BaseModel):
    post_time: datetime
    reason: str
    expected_reach: int


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-20250514",
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0.3,
    )


def run_scheduler_agent(analytics_data: list[dict] | None = None) -> ScheduleDecision:
    llm = _get_llm()

    analytics_block = ""
    if analytics_data:
        analytics_block = f"\n\nHistorical analytics data:\n{json.dumps(analytics_data, indent=2)}"

    messages = [
        SystemMessage(content=(
            "You are a data-driven social media scheduler who maximises reach for UPSC content on Instagram. "
            "UPSC aspirants are most active early morning (6-8 AM IST) and evening (7-10 PM IST). "
            "Always return valid JSON only, no markdown, no explanation."
        )),
        HumanMessage(content=(
            "Based on the analytics data provided, pick the single optimal posting time for the next Instagram post.\n"
            f"{analytics_block}\n\n"
            "Return a JSON object with:\n"
            "  post_time: ISO 8601 datetime string (use IST offset +05:30)\n"
            "  reason: one sentence explaining why this time was chosen\n"
            "  expected_reach: estimated reach as integer"
        )),
    ]

    logger.info("[SchedulerAgent] Calculating optimal post time")
    response = llm.invoke(messages)
    raw = response.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
        decision = ScheduleDecision(**data)
        logger.info(f"[SchedulerAgent] Scheduled for {decision.post_time}, expected reach={decision.expected_reach}")
        return decision
    except Exception as e:
        logger.error(f"[SchedulerAgent] Failed to parse response: {e}\nRaw: {raw}")
        raise
