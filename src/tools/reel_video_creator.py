"""
Reel video creator — generates a 30-second slideshow video from images + text.
Uses MoviePy (free, no API needed) + Pollinations.AI images (free).
Flow: script → 5 images → slideshow video → upload to R2 → post as Reel.
"""
import io
import os
import tempfile
import urllib.parse
from pathlib import Path

import httpx
from loguru import logger
from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def _load_font(size: int):
    for path in ["arial.ttf", "DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _create_text_slide(text: str, subtext: str = "", slide_num: int = 1, total: int = 5) -> bytes:
    """Create a 1080x1920 branded slide with text overlay."""
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), (7, 8, 15))  # #07080f
    draw = ImageDraw.Draw(img)

    # Purple gradient top bar
    for i in range(12):
        alpha = int(200 * (1 - i / 12))
        draw.rectangle([(0, i * 6), (w, (i + 1) * 6)], fill=(124, 58, 237))

    # Teal accent line
    draw.rectangle([(60, 90), (w - 60, 96)], fill=(0, 229, 195))

    # TOPPER IAS branding
    font_brand = _load_font(32)
    draw.text((60, 110), "TOPPER IAS", font=font_brand, fill=(0, 229, 195))

    # Main text (word-wrapped)
    font_main = _load_font(72)
    words = text.split()
    lines, line = [], []
    for word in words:
        test = " ".join(line + [word])
        bbox = draw.textbbox((0, 0), test, font=font_main)
        if bbox[2] - bbox[0] > w - 120:
            if line: lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line: lines.append(" ".join(line))

    y = h // 3
    for ln in lines[:5]:
        bbox = draw.textbbox((0, 0), ln, font=font_main)
        x = (w - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), ln, font=font_main, fill=(232, 234, 246))
        y += 90

    # Subtext
    if subtext:
        font_sub = _load_font(44)
        words_s = subtext.split()
        lines_s, line_s = [], []
        for word in words_s:
            test = " ".join(line_s + [word])
            bbox = draw.textbbox((0, 0), test, font=font_sub)
            if bbox[2] - bbox[0] > w - 120:
                if line_s: lines_s.append(" ".join(line_s))
                line_s = [word]
            else:
                line_s.append(word)
        if line_s: lines_s.append(" ".join(line_s))
        y += 30
        for ln in lines_s[:3]:
            bbox = draw.textbbox((0, 0), ln, font=font_sub)
            x = (w - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), ln, font=font_sub, fill=(74, 79, 114))
            y += 60

    # Slide indicator
    dot_y = h - 80
    for i in range(total):
        color = (0, 229, 195) if i == slide_num - 1 else (28, 31, 50)
        x = w // 2 - (total * 20) // 2 + i * 20
        draw.ellipse([(x, dot_y), (x + 12, dot_y + 12)], fill=color)

    # Bottom bar
    draw.rectangle([(0, h - 10), (w, h)], fill=(124, 58, 237))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


async def _fetch_pollinations_image(prompt: str, width: int = 1080, height: int = 1920) -> bytes | None:
    """Fetch an AI image from Pollinations.AI."""
    encoded = urllib.parse.quote(f"{prompt}, dark purple theme, educational, UPSC, professional")
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true"
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url)
        if resp.is_success and len(resp.content) > 1000:
            return resp.content
    except Exception as e:
        logger.warning(f"[ReelVideo] Pollinations fetch failed: {e}")
    return None


# ---------------------------------------------------------------------------
# Main video creator
# ---------------------------------------------------------------------------

async def create_reel_video(
    hook: str,
    value_points: list[str],
    cta: str,
    topic: str,
    duration_seconds: int = 30,
) -> str | None:
    """
    Create a 30-second slideshow reel video.
    Returns R2 public URL of the uploaded video, or None on failure.
    """
    try:
        from moviepy.editor import ImageClip, concatenate_videoclips, CompositeVideoClip
        import numpy as np
    except ImportError:
        logger.error("[ReelVideo] moviepy not installed")
        return None

    logger.info(f"[ReelVideo] Creating reel for topic='{topic}'")

    slides_text = [
        (hook, ""),
        (value_points[0] if len(value_points) > 0 else topic, "Key insight #1"),
        (value_points[1] if len(value_points) > 1 else topic, "Key insight #2"),
        (value_points[2] if len(value_points) > 2 else topic, "Key insight #3"),
        (cta, "Follow TOPPER IAS for daily UPSC tips"),
    ]

    total_slides = len(slides_text)
    slide_duration = duration_seconds / total_slides  # seconds per slide

    clips = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, (text, subtext) in enumerate(slides_text):
            # Try Pollinations image first, fall back to text slide
            img_bytes = await _fetch_pollinations_image(f"{text} UPSC preparation")
            if img_bytes:
                try:
                    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                    img = img.resize((1080, 1920), Image.LANCZOS)
                    # Add text overlay on top of the image
                    draw = ImageDraw.Draw(img)
                    # Semi-transparent overlay at bottom
                    overlay = Image.new("RGBA", (1080, 400), (7, 8, 15, 200))
                    img.paste(Image.fromarray(np.array(overlay)[:, :, :3]), (0, 1520))
                    font = _load_font(48)
                    words = text.split()
                    lines, line = [], []
                    for word in words:
                        test = " ".join(line + [word])
                        bbox = draw.textbbox((0, 0), test, font=font)
                        if bbox[2] - bbox[0] > 960:
                            if line: lines.append(" ".join(line))
                            line = [word]
                        else:
                            line.append(word)
                    if line: lines.append(" ".join(line))
                    y = 1540
                    for ln in lines[:3]:
                        bbox = draw.textbbox((0, 0), ln, font=font)
                        x = (1080 - (bbox[2] - bbox[0])) // 2
                        draw.text((x, y), ln, font=font, fill=(232, 234, 246))
                        y += 60
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="JPEG", quality=88)
                    img_bytes = img_bytes.getvalue()
                except Exception:
                    img_bytes = _create_text_slide(text, subtext, i + 1, total_slides)
            else:
                img_bytes = _create_text_slide(text, subtext, i + 1, total_slides)

            # Save frame as image file
            frame_path = os.path.join(tmpdir, f"frame_{i:02d}.jpg")
            with open(frame_path, "wb") as f:
                f.write(img_bytes)

            clip = ImageClip(frame_path, duration=slide_duration)
            clips.append(clip)

        if not clips:
            return None

        # Concatenate all clips
        video = concatenate_videoclips(clips, method="compose")
        video_path = os.path.join(tmpdir, "reel.mp4")
        video.write_videofile(
            video_path,
            fps=24,
            codec="libx264",
            audio=False,
            verbose=False,
            logger=None,
        )

        # Upload to R2
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        from src.tools.storage_tool import generate_filename, upload_media
        filename = generate_filename(topic, content_type="reel").replace(".jpg", ".mp4")
        url = upload_media(video_bytes, filename, content_type="video/mp4")
        logger.info(f"[ReelVideo] Video uploaded to R2: {url}")
        return url

    except Exception as e:
        logger.error(f"[ReelVideo] Failed to create video: {e}")
        return None
