"""
v3_engine/slide_renderer.py

Self-contained slide renderer for V3 pipeline.
Renders storyboard slides to PNG completely independently — zero dependency on V2 code.

Handles all visual_types from the lesson JSON storyboard:
  - title_slide
  - curriculum_map
  - architecture_diagram
  - code_snippet
  - terminal_output
  - sequence_diagram
  - concept_box
  - (fallback) generic text slide
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

# ─── Constants ─────────────────────────────────────────────────────────────────

W, H = 1920, 1080

# Dark tech color palette
BG_TOP     = (10, 14, 26)       # near-black navy
BG_BOT     = (15, 20, 40)       # deep dark blue
ACCENT     = (56, 189, 248)     # sky blue
ACCENT2    = (139, 92, 246)     # violet
GREEN      = (52, 211, 153)     # emerald
AMBER      = (251, 191, 36)     # amber
RED        = (248, 113, 113)    # soft red
TEXT_WHITE = (240, 248, 255)    # near-white
TEXT_DIM   = (148, 163, 184)    # slate-400
CODE_BG    = (20, 27, 45)       # code panel dark
TERM_BG    = (12, 16, 30)       # terminal dark


# ─── Font Helpers ───────────────────────────────────────────────────────────────

def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a system font by size. Prefers Helvetica/Arial, falls back to default."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _mono_font(size: int) -> ImageFont.FreeTypeFont:
    """Load a monospace font for code blocks."""
    candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/Library/Fonts/Courier New.ttf",
        "/System/Library/Fonts/Supplemental/CourierNew.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Word-wrap text to fit within max_w pixels."""
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_w and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


# ─── Background ─────────────────────────────────────────────────────────────────

def _draw_background(img: Image.Image) -> None:
    """Draw a dark gradient background with subtle grid lines."""
    draw = ImageDraw.Draw(img)

    # Vertical gradient via horizontal bands
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Subtle grid
    grid_color = (255, 255, 255, 10)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(0, W, 80):
        od.line([(x, 0), (x, H)], fill=grid_color)
    for y in range(0, H, 80):
        od.line([(0, y), (W, y)], fill=grid_color)
    img.paste(overlay, mask=overlay)

    # Bottom accent glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rectangle([(0, H - 4), (W, H)], fill=(*ACCENT, 180))
    img.paste(glow, mask=glow)


def _draw_title_bar(draw: ImageDraw.ImageDraw, title: str, subtitle: str = "") -> None:
    """Draw a stylized title section at top-left."""
    # Channel badge
    badge_font = _font(22)
    draw.text((90, 48), "⬡ Understanding AIML", font=badge_font, fill=(*ACCENT, 200))

    # Accent line under badge
    draw.line([(90, 82), (500, 82)], fill=ACCENT, width=2)

    # Main title
    title_font = _font(64, bold=True)
    draw.text((90, 100), title, font=title_font, fill=TEXT_WHITE)

    if subtitle:
        sub_font = _font(32)
        draw.text((90, 185), subtitle, font=sub_font, fill=TEXT_DIM)


# ─── Visual Type Renderers ──────────────────────────────────────────────────────

def _render_title_slide(img: Image.Image, slide: dict, lang: str) -> None:
    draw = ImageDraw.Draw(img)
    title = slide.get(f"title_{lang}") or slide.get("title_en", "")
    subtitle = slide.get(f"content_text_{lang}") or slide.get("content_text_en", "")

    # Large centered title
    tf = _font(80, bold=True)
    lines = textwrap.wrap(title, 30)
    y = 350
    for line in lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=tf)
        x = (W - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=tf, fill=TEXT_WHITE)
        y += 100

    # Centered underline
    draw.line([(W // 2 - 200, y + 10), (W // 2 + 200, y + 10)], fill=ACCENT, width=3)
    y += 40

    # Subtitle
    sf = _font(38)
    sub_lines = textwrap.wrap(subtitle or "", 50)
    for line in sub_lines[:2]:
        bbox = draw.textbbox((0, 0), line, font=sf)
        x = (W - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=sf, fill=TEXT_DIM)
        y += 52

    # Channel branding at bottom
    bf = _font(28)
    draw.text((W // 2 - 180, H - 80), "⬡ Understanding AIML", font=bf, fill=(*ACCENT2, 200))


def _render_code_snippet(img: Image.Image, slide: dict, lang: str) -> None:
    draw = ImageDraw.Draw(img)
    title = slide.get(f"title_{lang}") or slide.get("title_en", "")
    narration = slide.get(f"narration_text_{lang}") or slide.get("narration_text_en", "")
    code = slide.get("visual_content", "")
    if isinstance(code, dict):
        code = code.get("code", "")

    _draw_title_bar(draw, title)

    # Code panel
    panel_x, panel_y = 80, 240
    panel_w, panel_h = W - 160, H - 290

    # Panel shadow
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        [(panel_x + 6, panel_y + 6), (panel_x + panel_w + 6, panel_y + panel_h + 6)],
        radius=12, fill=(0, 0, 0, 120)
    )
    img.paste(shadow, mask=shadow)

    # Panel bg
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle(
        [(panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h)],
        radius=12, fill=(*CODE_BG, 245)
    )
    img.paste(panel, mask=panel)

    # Traffic lights
    for ci, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = panel_x + 22 + ci * 22
        draw.ellipse([(cx - 7, panel_y + 14), (cx + 7, panel_y + 28)], fill=col)

    # Filename tab
    draw.text((panel_x + 80, panel_y + 10), "lesson_demo.py", font=_font(22), fill=TEXT_DIM)
    draw.line([(panel_x + 80, panel_y + 36), (panel_x + 80 + 180, panel_y + 36)], fill=ACCENT, width=2)

    # Code text
    code_font = _mono_font(26)
    cx, cy = panel_x + 24, panel_y + 52
    line_h = 34
    KEYWORD_COLOR = (197, 134, 192)
    STRING_COLOR  = (206, 145, 120)
    COMMENT_COLOR = (106, 153, 85)
    NUMBER_COLOR  = (181, 206, 168)
    KEYWORDS = {"def", "class", "import", "from", "return", "if", "else", "elif",
                "for", "while", "try", "except", "with", "as", "in", "not", "and",
                "or", "True", "False", "None", "self", "print", "raise"}

    for raw_line in (code or "").splitlines():
        if cy > panel_y + panel_h - 10:
            break
        stripped = raw_line.rstrip()

        if stripped.lstrip().startswith("#"):
            draw.text((cx, cy), stripped, font=code_font, fill=COMMENT_COLOR)
        elif stripped.lstrip().startswith(('"""', "'''")):
            draw.text((cx, cy), stripped, font=code_font, fill=STRING_COLOR)
        else:
            # Simple tokenizer: color keywords
            tokens = stripped.split(" ")
            tx = cx
            for token in tokens:
                color = TEXT_WHITE
                bare = token.strip("():,.")
                if bare in KEYWORDS:
                    color = KEYWORD_COLOR
                elif token.startswith('"') or token.startswith("'"):
                    color = STRING_COLOR
                elif token.isdigit():
                    color = NUMBER_COLOR
                draw.text((tx, cy), token + " ", font=code_font, fill=color)
                bbox = draw.textbbox((0, 0), token + " ", font=code_font)
                tx += bbox[2] - bbox[0]
        cy += line_h


def _render_terminal_output(img: Image.Image, slide: dict, lang: str) -> None:
    draw = ImageDraw.Draw(img)
    title = slide.get(f"title_{lang}") or slide.get("title_en", "")
    content = slide.get("visual_content", "")
    if isinstance(content, dict):
        content = str(content)

    _draw_title_bar(draw, title)

    # Terminal panel
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    px, py, pw, ph = 80, 240, W - 160, H - 290
    pd.rounded_rectangle([(px, py), (px + pw, py + ph)], radius=10, fill=(*TERM_BG, 250))
    img.paste(panel, mask=panel)

    # Terminal header
    draw.rectangle([(px, py), (px + pw, py + 40)], fill=(30, 35, 55))
    draw.text((px + 16, py + 10), "$ bash — Terminal", font=_font(22), fill=TEXT_DIM)

    # Terminal content
    tf = _mono_font(28)
    tx, ty = px + 20, py + 56
    lh = 36
    for line in str(content).splitlines():
        if ty > py + ph - 10:
            break
        color = GREEN if line.startswith("$") else (RED if "Error" in line or "Traceback" in line else TEXT_WHITE)
        if "✅" in line or "Done" in line or "Success" in line:
            color = GREEN
        draw.text((tx, ty), line, font=tf, fill=color)
        ty += lh


def _render_text_slide(img: Image.Image, slide: dict, lang: str) -> None:
    """Generic fallback renderer for concept_box, curriculum_map, etc."""
    draw = ImageDraw.Draw(img)
    title = slide.get(f"title_{lang}") or slide.get("title_en", "")
    content = slide.get(f"content_text_{lang}") or slide.get("content_text_en", "")
    visual_content = slide.get("visual_content", "")

    _draw_title_bar(draw, title)

    # Content text area
    body_font = _font(36)
    bullet_font = _font(32)
    y = 250
    max_w = W - 200

    if content:
        lines = _wrap(content, body_font, max_w, draw)
        for line in lines[:12]:
            draw.text((100, y), line, font=body_font, fill=TEXT_WHITE)
            y += 50

    y += 20

    # Visual content (if dict with list items, render as bullets)
    if isinstance(visual_content, dict):
        items = []
        for v in visual_content.values():
            if isinstance(v, list):
                items = v
                break
        for item in items[:8]:
            txt = f"  ▸  {item}" if isinstance(item, str) else f"  ▸  {str(item)[:80]}"
            draw.text((100, y), txt, font=bullet_font, fill=ACCENT)
            y += 48
    elif isinstance(visual_content, list):
        for item in visual_content[:8]:
            txt = f"  ▸  {str(item)[:90]}"
            draw.text((100, y), txt, font=bullet_font, fill=ACCENT)
            y += 48
    elif isinstance(visual_content, str) and visual_content:
        lines = _wrap(visual_content, bullet_font, max_w, draw)
        for line in lines[:6]:
            draw.text((100, y), f"  ▸  {line}", font=bullet_font, fill=TEXT_DIM)
            y += 48


# ─── Main Entry Point ───────────────────────────────────────────────────────────

def render_slide(slide: dict, output_path: str, lang: str = "en") -> bool:
    """
    Render a single storyboard slide to a flat PNG file.

    Args:
        slide: The slide dict from the lesson storyboard.
        output_path: Where to save the PNG.
        lang: "en" or "hi"

    Returns:
        True if rendering succeeded.
    """
    visual_type = slide.get("visual_type", "")

    img = Image.new("RGBA", (W, H), BG_TOP)
    _draw_background(img)

    try:
        if visual_type == "title_slide":
            _render_title_slide(img, slide, lang)
        elif visual_type == "code_snippet":
            _render_code_snippet(img, slide, lang)
        elif visual_type == "terminal_output":
            _render_terminal_output(img, slide, lang)
        else:
            # curriculum_map, architecture_diagram (no Imagen), concept_box, sequence_diagram
            _render_text_slide(img, slide, lang)

        img.convert("RGB").save(output_path)
        return True

    except Exception as e:
        print(f"  [slide_renderer] ❌ Failed to render slide ({visual_type}): {e}")
        # Save a minimal error slide
        draw = ImageDraw.Draw(img)
        draw.text((100, 500), f"⚠️  Slide render error: {e}", font=_font(36), fill=RED)
        img.convert("RGB").save(output_path)
        return False


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python slide_renderer.py <lesson.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        lesson = json.load(f)

    slides = lesson.get("storyboard") or lesson.get("slides", [])
    lang = sys.argv[2] if len(sys.argv) > 2 else "en"

    print(f"Rendering {len(slides)} slides...")
    for i, slide in enumerate(slides):
        out = f"/tmp/v3_preview_slide_{i:02d}.png"
        ok = render_slide(slide, out, lang=lang)
        vtype = slide.get("visual_type", "unknown")
        print(f"  [{i}] {vtype} → {out} {'✅' if ok else '❌'}")

    print("Done! Open /tmp/v3_preview_slide_*.png to review.")
