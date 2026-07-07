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


def _render_architecture_diagram(img: Image.Image, slide: dict, lang: str) -> None:
    """Render a visual box-and-arrow architecture diagram."""
    draw = ImageDraw.Draw(img)
    title = slide.get(f"title_{lang}") or slide.get("title_en", "")
    visual_content = slide.get("visual_content", {})

    _draw_title_bar(draw, title)

    # Extract steps / components from visual_content
    steps = []
    if isinstance(visual_content, dict):
        for key in ("steps", "stages", "components", "nodes", "flow"):
            if key in visual_content:
                steps = visual_content[key]
                break
        if not steps:
            steps = [f"{k}: {v}" for k, v in visual_content.items() if isinstance(v, str)]
    elif isinstance(visual_content, list):
        steps = visual_content
    elif isinstance(visual_content, str):
        steps = [line.strip() for line in visual_content.splitlines() if line.strip()]

    if not steps:
        # Nothing to draw — show narration as text instead
        content = slide.get(f"narration_text_{lang}") or slide.get("narration_text_en", "")
        bf = _font(36)
        y = 270
        for line in _wrap(content, bf, W - 200, draw)[:10]:
            draw.text((100, y), line, font=bf, fill=TEXT_WHITE)
            y += 52
        return

    # Layout: horizontal pipeline boxes with arrows
    n = min(len(steps), 6)
    steps = steps[:n]

    box_w = min(280, (W - 200) // n - 30)
    box_h = 140
    spacing = (W - 160 - n * box_w) // (n + 1)
    start_x = 80 + spacing
    cy = 550  # vertical center

    COLORS = [ACCENT, ACCENT2, GREEN, AMBER, RED, (251, 113, 133)]

    for i, step in enumerate(steps):
        bx = start_x + i * (box_w + spacing)
        by = cy - box_h // 2
        color = COLORS[i % len(COLORS)]

        # Shadow
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle([(bx + 5, by + 5), (bx + box_w + 5, by + box_h + 5)], radius=12, fill=(0, 0, 0, 100))
        img.paste(shadow, mask=shadow)

        # Box
        panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel)
        pd.rounded_rectangle([(bx, by), (bx + box_w, by + box_h)], radius=12, fill=(*CODE_BG, 230))
        pd.rounded_rectangle([(bx, by), (bx + box_w, by + box_h)], radius=12, outline=(*color, 200), width=2)
        # Top color bar
        pd.rounded_rectangle([(bx, by), (bx + box_w, by + 8)], radius=4, fill=(*color, 220))
        img.paste(panel, mask=panel)

        # Number badge
        draw.ellipse([(bx + 14, by + 18), (bx + 38, by + 42)], fill=color)
        nf = _font(18)
        draw.text((bx + 21, by + 20), str(i + 1), font=nf, fill=(0, 0, 0))

        # Step text
        tf = _font(24)
        label = str(step)[:60]
        lines = _wrap(label, tf, box_w - 20, draw)
        ty = by + 52
        for line in lines[:3]:
            draw.text((bx + 10, ty), line, font=tf, fill=TEXT_WHITE)
            ty += 30

        # Arrow → next box
        if i < n - 1:
            ax = bx + box_w + 8
            ay = cy
            draw.line([(ax, ay), (ax + spacing - 8, ay)], fill=(*ACCENT, 200), width=3)
            # Arrowhead
            draw.polygon([
                (ax + spacing - 6, ay - 8),
                (ax + spacing + 6, ay),
                (ax + spacing - 6, ay + 8),
            ], fill=(*ACCENT, 200))

    # Label below boxes
    lf = _font(26)
    content = slide.get(f"content_text_{lang}") or slide.get("content_text_en", "")
    if content:
        lines = _wrap(content, lf, W - 200, draw)[:3]
        y = cy + box_h // 2 + 30
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=lf)
            x = (W - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=lf, fill=TEXT_DIM)
            y += 38


def _render_sequence_diagram(img: Image.Image, slide: dict, lang: str) -> None:
    """Render a vertical sequence of steps with numbered items and icons."""
    draw = ImageDraw.Draw(img)
    title = slide.get(f"title_{lang}") or slide.get("title_en", "")
    visual_content = slide.get("visual_content", {})
    content = slide.get(f"content_text_{lang}") or slide.get("content_text_en", "")

    _draw_title_bar(draw, title)

    steps = []
    if isinstance(visual_content, dict):
        for key in ("steps", "sequence", "flow", "stages"):
            if key in visual_content:
                steps = visual_content[key]
                break
        if not steps:
            steps = [f"{k}: {v}" for k, v in visual_content.items() if isinstance(v, str)]
    elif isinstance(visual_content, list):
        steps = visual_content
    elif isinstance(visual_content, str):
        steps = [l.strip() for l in visual_content.splitlines() if l.strip()]

    if not steps and content:
        steps = [l.strip("- •* ") for l in content.splitlines() if l.strip()]

    sf = _font(32)
    nf = _font(26)
    COLORS = [ACCENT, GREEN, ACCENT2, AMBER, RED]
    px, py = 200, 240
    step_h = min(100, (H - 320) // max(len(steps), 1))
    lx = px + 30  # vertical timeline x

    # Vertical line
    draw.line([(lx, py), (lx, py + len(steps[:8]) * step_h)], fill=(*TEXT_DIM, 100), width=2)

    for i, step in enumerate(steps[:8]):
        y = py + i * step_h
        color = COLORS[i % len(COLORS)]

        # Circle on timeline
        draw.ellipse([(lx - 12, y + 4), (lx + 12, y + 28)], fill=color)
        draw.text((lx - 6, y + 6), str(i + 1), font=_font(18), fill=(0, 0, 0))

        # Step label
        label = str(step)
        lines = _wrap(label, sf, W - 400, draw)[:2]
        ty = y + 4
        for line in lines:
            draw.text((lx + 30, ty), line, font=sf, fill=TEXT_WHITE)
            ty += 36

        # Connector
        if i < len(steps) - 1:
            draw.line([(lx, y + 28), (lx, y + step_h)], fill=(*TEXT_DIM, 80), width=2)


def _render_curriculum_map(img: Image.Image, slide: dict, lang: str) -> None:
    """Render a curriculum map as a two-column grid of lesson cards."""
    draw = ImageDraw.Draw(img)
    title = slide.get(f"title_{lang}") or slide.get("title_en", "")
    visual_content = slide.get("visual_content", {})
    content = slide.get(f"content_text_{lang}") or slide.get("content_text_en", "")

    _draw_title_bar(draw, title)

    items = []
    if isinstance(visual_content, dict):
        items = [f"{k}: {v}" for k, v in visual_content.items()]
    elif isinstance(visual_content, list):
        items = [str(i) for i in visual_content]
    elif isinstance(visual_content, str):
        items = [l.strip() for l in visual_content.splitlines() if l.strip()]
    if not items and content:
        items = [l.strip("- •*") for l in content.splitlines() if l.strip()]

    # 2-column grid
    cols = 2
    col_w = (W - 200) // cols - 20
    card_h = 90
    pad_x, pad_y = 90, 250
    COLORS = [ACCENT, ACCENT2, GREEN, AMBER, RED, (251, 113, 133)]

    for i, item in enumerate(items[:8]):
        col = i % cols
        row = i // cols
        bx = pad_x + col * (col_w + 30)
        by = pad_y + row * (card_h + 20)
        color = COLORS[i % len(COLORS)]

        # Card
        panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel)
        pd.rounded_rectangle([(bx, by), (bx + col_w, by + card_h)], radius=10, fill=(*CODE_BG, 220))
        pd.rounded_rectangle([(bx, by), (bx + 6, by + card_h)], radius=4, fill=(*color, 220))
        img.paste(panel, mask=panel)

        draw.text((bx + 20, by + 12), str(item)[:80], font=_font(28), fill=TEXT_WHITE)
        # Index
        draw.text((bx + col_w - 40, by + 12), f"#{i+1:02d}", font=_font(24), fill=color)


def _render_concept_box(img: Image.Image, slide: dict, lang: str) -> None:
    """Render a concept explanation with highlighted box and bullet points."""
    draw = ImageDraw.Draw(img)
    title = slide.get(f"title_{lang}") or slide.get("title_en", "")
    content = slide.get(f"content_text_{lang}") or slide.get("content_text_en", "")
    visual_content = slide.get("visual_content", {})

    _draw_title_bar(draw, title)

    # Main explanation box
    if content:
        panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel)
        pd.rounded_rectangle([(80, 240), (W - 80, 420)], radius=14, fill=(*CODE_BG, 220))
        pd.rounded_rectangle([(80, 240), (86, 420)], radius=4, fill=(*ACCENT, 240))
        img.paste(panel, mask=panel)

        cf = _font(34)
        lines = _wrap(content, cf, W - 200, draw)
        y = 260
        for line in lines[:4]:
            draw.text((100, y), line, font=cf, fill=TEXT_WHITE)
            y += 44

    # Bullet points below
    bullets = []
    if isinstance(visual_content, dict):
        for k, v in visual_content.items():
            bullets.append(f"{k}: {v}" if isinstance(v, str) else str(v)[:80])
    elif isinstance(visual_content, list):
        bullets = [str(b) for b in visual_content]
    elif isinstance(visual_content, str):
        bullets = [l.strip("- •*") for l in visual_content.splitlines() if l.strip()]

    bf = _font(30)
    y = 450
    for b in bullets[:6]:
        # Bullet marker
        draw.ellipse([(90, y + 12), (104, y + 26)], fill=ACCENT)
        draw.text((118, y), str(b)[:100], font=bf, fill=TEXT_DIM)
        y += 50


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
        elif visual_type == "architecture_diagram":
            _render_architecture_diagram(img, slide, lang)
        elif visual_type == "sequence_diagram":
            _render_sequence_diagram(img, slide, lang)
        elif visual_type == "curriculum_map":
            _render_curriculum_map(img, slide, lang)
        elif visual_type == "concept_box":
            _render_concept_box(img, slide, lang)
        else:
            _render_concept_box(img, slide, lang)  # best generic fallback

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
