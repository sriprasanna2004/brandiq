import os

from loguru import logger

INTENT_KEYWORDS = {"fees", "batch", "admission", "join", "cost", "price", "register", "enroll"}


def verify_webhook(mode: str, token: str, challenge: str) -> str | None:
    verify_token = os.getenv("META_VERIFY_TOKEN", "")
    if mode == "subscribe" and token == verify_token:
        logger.info("[Webhook] Instagram webhook verified")
        return challenge
    logger.warning(f"[Webhook] Verification failed: mode={mode}, token_match={token == verify_token}")
    return None


async def handle_instagram_event(payload: dict) -> dict:
    from src.scheduler.tasks import run_lead_crew_task

    try:
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # ----------------------------------------------------------------
        # DM (messaging)
        # ----------------------------------------------------------------
        messages = value.get("messages", [])
        if messages:
            msg = messages[0]
            sender_id = msg.get("from", "")
            message_text = msg.get("text", {}).get("body", "") if msg.get("type") == "text" else ""

            logger.info(f"[Webhook] DM from {sender_id}: {message_text[:80]}")

            # Dispatch lead scoring task
            run_lead_crew_task.delay(
                ig_handle=sender_id,
                message_text=message_text,
                day_number=0,
            )

            # Hot lead alert — check keywords locally for immediate Telegram ping
            text_lower = message_text.lower()
            found = [kw for kw in INTENT_KEYWORDS if kw in text_lower]
            if found:
                from src.tools.telegram_tool import send_hot_lead_alert
                await send_hot_lead_alert(
                    ig_handle=sender_id,
                    keywords=found,
                    auto_reply="Lead scoring task queued",
                )

            return {"status": "processed", "type": "dm", "sender": sender_id}

        # ----------------------------------------------------------------
        # Comment
        # ----------------------------------------------------------------
        comments = value.get("comments", [])
        if comments:
            comment = comments[0]
            sender_id = comment.get("from", {}).get("id", "")
            comment_text = comment.get("text", "")

            logger.info(f"[Webhook] Comment from {sender_id}: {comment_text[:80]}")

            text_lower = comment_text.lower()
            found = [kw for kw in INTENT_KEYWORDS if kw in text_lower]
            if found:
                logger.info(f"[Webhook] Intent keywords in comment: {found}")
                run_lead_crew_task.delay(
                    ig_handle=sender_id,
                    message_text=comment_text,
                    day_number=0,
                )
                return {"status": "processed", "type": "comment", "intent": found}

            return {"status": "ignored", "type": "comment", "reason": "no_intent"}

    except Exception as e:
        logger.error(f"[Webhook] Error handling Instagram event: {e}")
        return {"status": "error", "detail": str(e)}

    return {"status": "ignored", "type": "unknown"}
