import os
import json
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

DAY_CONTEXT = {
    1:  "warm welcome + batch details + what makes TOPPER IAS different from other coaching institutes",
    3:  "introduce Adaptiq app + free trial link + personalised weak area analysis feature",
    7:  "urgency message + limited seats available + batch starting soon",
    14: "final CTA + share a topper success story + direct admission link",
}


class NurtureMessage(BaseModel):
    message: str        # under 500 chars
    template_name: str
    variables: dict


def _get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.7,
    )


def run_lead_nurture_agent(lead_name: str, day_number: int, lead_status: str) -> NurtureMessage:
    if day_number not in DAY_CONTEXT:
        raise ValueError(f"day_number must be one of {list(DAY_CONTEXT.keys())}, got {day_number}")

    context = DAY_CONTEXT[day_number]
    llm = _get_llm()
    messages = [
        SystemMessage(content=(
            "You are an empathetic student counsellor for TOPPER IAS who understands the UPSC journey deeply. "
            "Write WhatsApp messages that feel personal, warm, and motivating — never salesy or pushy. "
            "Keep messages under 500 characters. "
            "Always return valid JSON only, no markdown, no explanation."
        )),
        HumanMessage(content=(
            f"Write a Day {day_number} WhatsApp nurture message for a UPSC aspirant.\n\n"
            f"Lead name: {lead_name}\n"
            f"Lead status: {lead_status}\n"
            f"Day {day_number} focus: {context}\n\n"
            "Return a JSON object with:\n"
            "  message: the WhatsApp message text (under 500 chars, use lead name, feel personal)\n"
            f"  template_name: snake_case template name like 'day_{day_number}_nurture'\n"
            "  variables: dict of dynamic variables used in the message (e.g. {\"name\": lead_name})"
        )),
    ]

    logger.info(f"[LeadNurtureAgent] Generating Day {day_number} message for {lead_name} (status={lead_status})")
    response = llm.invoke(messages)
    raw = response.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
        msg = NurtureMessage(**data)
        logger.info(f"[LeadNurtureAgent] Message ready, template={msg.template_name}")
        return msg
    except Exception as e:
        logger.error(f"[LeadNurtureAgent] Failed to parse response: {e}\nRaw: {raw}")
        raise

