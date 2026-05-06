"""
Reel video creator — generates a 30-second slideshow video from images + text.
Uses OpenCV + imageio (no moviepy needed) + Pollinations.AI images (free).
Flow: script → 5 slides → MP4 video → upload to R2 → post as Reel.
"""
import io
import os
import tempfile
import urllib.parse

import httpx
import numpy as np
from loguru import logger
from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_font(size: int):
    for path in [
        "arial.ttf", "DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _create_text_slide(text: str, subtext: str = "", slide_num: int = 1, total: int = 5) -> np.ndarray:
    """Create a 1080x1920 branded slide. Returns numpy array (RGB)."""
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), (7, 8, 15))
    draw = ImageDraw.Draw(img)

    # Purple top bar
    for i in range(10):
        draw.rectangle([(0, i * 8), (w, (i + 1) * 8)], fill=(124, 58, 237))

    # Teal accent line
    draw.rectangle([(60, 90), (w - 60, 96)], fill=(0, 229, 195))

    # Brand
    font_brand = _load_font(34)
    draw.text((60, 110), "TOPPER IAS", font=font_brand, fill=(0, 229, 195))

    # Main text
    font_main = _load_font(68)
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
        y += 88

    # Subtext
    if subtext:
        font_sub = _load_font(42)
        y += 20
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
        for ln in lines_s[:3]:
            bbox = draw.textbbox((0, 0), ln, font=font_sub)
            x = (w - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), ln, font=font_sub, fill=(74, 79, 114))
            y += 58

    # Slide dots
    dot_y = h - 80
    for i in range(total):
        color = (0, 229, 195) if i == slide_num - 1 else (28, 31, 50)
        x = w // 2 - (total * 22) // 2 + i * 22
        draw.ellipse([(x, dot_y), (x + 14, dot_y + 14)], fill=color)

    # Bottom bar
    draw.rectangle([(0, h - 10), (w, h)], fill=(124, 58, 237))

    return np.array(img)


async def _fetch_image_as_array(prompt: str) -> np.ndarray | None:
    """Fetch Pollinations image and return as numpy array."""
    encoded = urllib.parse.quote(f"{prompt}, dark purple educational UPSC professional")
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true"
    try:
        async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
            resp = await client.get(url)
        if resp.is_success and len(resp.content) > 5000:
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            img = img.resize((1080, 1920), Image.LANCZOS)
            return np.array(img)
    except Exception as e:
        logger.warning(f"[ReelVideo] Pollinations failed: {e}")
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def create_reel_video(
    hook: str,
    value_points: list[str],
    cta: str,
    topic: str,
    duration_seconds: int = 30,
) -> str | None:
    """
    Create a slideshow reel video using imageio + ffmpeg.
    Returns R2 public URL or None on failure.
    """
    try:
        import imageio
    except ImportError:
        logger.error("[ReelVideo] imageio not installed")
        return None

    logger.info(f"[ReelVideo] Creating {duration_seconds}s reel for '{topic}'")

    slides = [
        (hook, ""),
        (value_points[0] if len(value_points) > 0 else topic, "Tip #1"),
        (value_points[1] if len(value_points) > 1 else topic, "Tip #2"),
        (value_points[2] if len(value_points) > 2 else topic, "Tip #3"),
        (cta, "Follow TOPPER IAS 🎯"),
    ]

    fps = 24
    slide_duration = duration_seconds / len(slides)
    frames_per_slide = int(fps * slide_duration)

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            video_path = tmp.name

        writer = imageio.get_writer(
            video_path, fps=fps,
            output_params=["-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "28"],
        )

        for i, (text, subtext) in enumerate(slides):
            logger.info(f"[ReelVideo] Generating slide {i+1}/{len(slides)}")

            # Try Pollinations image, fall back to text slide
            frame = await _fetch_image_as_array(f"{text} UPSC preparation")
            if frame is None:
                frame = _create_text_slide(text, subtext, i + 1, len(slides))
            else:
                # Add text overlay on Pollinations image
                img = Image.fromarray(frame)
                draw = ImageDraw.Draw(img)
                # Dark overlay at bottom third
                overlay = Image.new("RGBA", (1080, 600), (7, 8, 15, 210))
                img_rgba = img.convert("RGBA")
                img_rgba.paste(overlay, (0, 1320), overlay)
                img = img_rgba.convert("RGB")
                draw = ImageDraw.Draw(img)
                font = _load_font(52)
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
                y = 1340
                for ln in lines[:4]:
                    bbox = draw.textbbox((0, 0), ln, font=font)
                    x = (1080 - (bbox[2] - bbox[0])) // 2
                    draw.text((x, y), ln, font=font, fill=(232, 234, 246))
                    y += 64
                # Watermark
                font_w = _load_font(28)
                draw.text((60, 1880), "TOPPER IAS", font=font_w, fill=(0, 229, 195))
                frame = np.array(img)

            for _ in range(frames_per_slide):
                writer.append_data(frame)

        writer.close()

        # Upload to R2
        with open(video_path, "rb") as f:
            video_bytes = f.read()
        os.unlink(video_path)

        from src.tools.storage_tool import generate_filename, upload_media
        filename = generate_filename(topic, content_type="reel").replace(".jpg", ".mp4")
        url = upload_media(video_bytes, filename, content_type="video/mp4")
        logger.info(f"[ReelVideo] Uploaded to R2: {url} ({len(video_bytes)//1024}KB)")
        return url

    except Exception as e:
        logger.error(f"[ReelVideo] Failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            os.unlink(video_path)
        except Exception:
            pass
        return None
