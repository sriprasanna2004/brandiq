import base64
import io
import os

import httpx
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from src.tools.storage_tool import generate_filename, upload_media

STABILITY_API_URL = (
    "https://api.stability.ai/v1/generation/"
    "stable-diffusion-xl-1024-v1-0/text-to-image"
)
BRAND_SUFFIX = (
    "educational poster style, purple and dark theme, "
    "professional, UPSC exam preparation, no text overlays"
)


async def generate_image(prompt: str, topic: str) -> str:
    api_key = os.getenv("STABILITY_API_KEY", "")
    if not api_key or api_key == "REPLACE_ME":
        logger.warning("[Visual] STABILITY_API_KEY not set, using placeholder")
        return f"https://via.placeholder.com/1024x1024.png?text={topic.replace(' ', '+')}"

    full_prompt = f"{prompt}, {BRAND_SUFFIX}"

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            STABILITY_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "text_prompts": [{"text": full_prompt, "weight": 1.0}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
                "steps": 30,
            },
        )

    if not resp.is_success:
        error_body = resp.text
        if resp.status_code == 429 or "insufficient_balance" in error_body:
            logger.warning(f"[Visual] Stability AI out of credits, using placeholder image")
            return f"https://via.placeholder.com/1024x1024/0d0f1a/00e5c3?text=TOPPER+IAS"
        raise Exception(
            f"Stability AI error: status={resp.status_code} body={error_body}"
        )

    data = resp.json()
    image_b64 = data["artifacts"][0]["base64"]
    image_bytes = base64.b64decode(image_b64)

    # Add watermark
    watermarked = add_watermark(image_bytes)

    # Try R2 upload — fall back to base64 data URL if R2 not configured
    r2_account = os.getenv("R2_ACCOUNT_ID", "REPLACE_ME")
    if r2_account and r2_account != "REPLACE_ME":
        try:
            from src.tools.storage_tool import generate_filename, upload_media
            filename = generate_filename(topic, content_type="post")
            url = upload_media(watermarked, filename, content_type="image/jpeg")
            logger.info(f"[Visual] Image uploaded to R2: {url}")
            return url
        except Exception as e:
            logger.warning(f"[Visual] R2 upload failed ({e}), using base64 data URL")

    # Fallback: return base64 data URL (works without R2)
    b64 = base64.b64encode(watermarked).decode()
    data_url = f"data:image/jpeg;base64,{b64}"
    logger.info(f"[Visual] Image generated as base64 data URL for topic='{topic}'")
    return data_url


def add_watermark(image_bytes: bytes, text: str = "TOPPER IAS") -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font = ImageFont.load_default()

    # Measure text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    margin = 16
    x = img.width - text_w - margin
    y = img.height - text_h - margin

    # Semi-transparent white text
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 180))

    watermarked = Image.alpha_composite(img, overlay).convert("RGB")
    buf = io.BytesIO()
    watermarked.save(buf, format="JPEG", quality=92)
    return buf.getvalue()
