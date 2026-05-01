import os
import json
from typing import Optional
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

DAY_CONTEXT = {
    1: "welcome to trial + how to use Adaptiq + what to expect in the next 7 days",
    3: "personalised weak area report based on their subjects + specific improvement tips",
    5: "progress update + show 15-25% improvement in weak areas + motivate to keep going",
    7: "trial ending tomorrow + upgrade CTA + special limited-time discount offer",
}


class AdaptiqMessage(BaseModel):
    message: str
    cta_link: str
    subject_tips: Optional[list[str]] = None


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-20250514",
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0.7,
    )


def run_adaptiq_promo_agent(
    lead_name: str,
    trial_day: int,
    weak_subjects: list[str],
) -> AdaptiqMessage:
    if trial_day not in DAY_CONTEXT:
        raise ValueError(f"trial_day must be one of {list(DAY_CONTEXT.keys())}, got {trial_day}")

    context = DAY_CONTEXT[trial_day]
    llm = _get_llm()
    messages = [
        SystemMessage(content=(
            "You are a growth hacker for Adaptiq, an AI-powered UPSC preparation app by TOPPER IAS. "
            "Write conversion-focused messages that feel personal and helpful, not pushy. "
            "Adaptiq's key features: AI-generated personalised study plans, weak area analysis, "
            "adaptive mock tests, and performance tracking. "
            "Always return valid JSON only, no markdown, no explanation."
        )),
        HumanMessage(content=(
            f"Write a Day {trial_day} Adaptiq trial message.\n\n"
            f"User name: {lead_name}\n"
            f"Weak subjects: {', '.join(weak_subjects) if weak_subjects else 'not yet assessed'}\n"
            f"Day {trial_day} focus: {context}\n\n"
            "Return a JSON object with:\n"
            "  message: the message text (warm, personal, under 400 chars)\n"
            "  cta_link: appropriate deep link like 'https://adaptiq.app/trial' or 'https://adaptiq.app/upgrade'\n"
            "  subject_tips: list of 2-3 quick tips for their weak subjects (null if day 1 or 7)"
        )),
    ]

    logger.info(f"[AdaptiqPromoAgent] Generating Day {trial_day} message for {lead_name}, weak={weak_subjects}")
    response = llm.invoke(messages)
    raw = response.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
        msg = AdaptiqMessage(**data)
        logger.info(f"[AdaptiqPromoAgent] Message ready, cta={msg.cta_link}")
        return msg
    except Exception as e:
        logger.error(f"[AdaptiqPromoAgent] Failed to parse response: {e}\nRaw: {raw}")
        raise
