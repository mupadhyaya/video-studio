import os
import base64
import zlib
import urllib.request
import io
from PIL import Image, ImageDraw, ImageFont

def get_font(font_name="Arial.ttf", size=36):
    font_paths = [
        # Check local assets for bundled fonts (e.g. Hind for Hindi support)
        f"assets/fonts/{font_name}",
        "assets/fonts/Hind-Regular.ttf",
        # Standard system fallbacks
        f"/System/Library/Fonts/Supplemental/{font_name}",
        f"/Library/Fonts/{font_name}",
        f"/System/Library/Fonts/{font_name}",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        f"/usr/share/fonts/TTF/{font_name}",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        try:
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]
        except AttributeError:
            width, _ = font.getsize(test_line)
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def draw_code_block(draw, width, height, code_text):
    box_x = int(width * 0.55)
    box_y = int(height * 0.2)
    box_w = int(width * 0.4)
    box_h = int(height * 0.6)
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=15, fill="#1E293B", outline="#334155", width=3)
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + 40], radius=15, fill="#334155")
    draw.ellipse([box_x + 15, box_y + 12, box_x + 31, box_y + 28], fill="#EF4444")
    draw.ellipse([box_x + 40, box_y + 12, box_x + 56, box_y + 28], fill="#F59E0B")
    draw.ellipse([box_x + 65, box_y + 12, box_x + 81, box_y + 28], fill="#10B981")
    if code_text:
        code_font = get_font("Courier New.ttf", 24)
        if isinstance(code_font, ImageFont.ImageFont):
            code_font = get_font("Arial.ttf", 24)
        lines = str(code_text).split('\n')
        wrapped_lines = []
        for line in lines:
            wrapped_lines.extend(wrap_text(line, code_font, box_w - 40))
        text_y = box_y + 60
        for line in wrapped_lines:
            draw.text((box_x + 20, text_y), line, font=code_font, fill="#A78BFA")
            text_y += 35
            if text_y > box_y + box_h - 40:
                break

def draw_terminal_output(draw, width, height, terminal_text):
    box_x = int(width * 0.55)
    box_y = int(height * 0.2)
    box_w = int(width * 0.4)
    box_h = int(height * 0.6)
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=10, fill="#0F172A", outline="#1E293B", width=3)
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + 35], radius=10, fill="#1E293B")
    
    font = get_font("Arial Unicode.ttf", 20)
    draw.text((box_x + box_w // 2 - 50, box_y + 5), "bash - Terminal", fill="#94A3B8", font=font)
    
    if terminal_text:
        term_font = get_font("Courier New.ttf", 22)
        if isinstance(term_font, ImageFont.ImageFont):
            term_font = get_font("Arial.ttf", 22)
        
        terminal_text = str(terminal_text)
        terminal_text = terminal_text.replace("```bash", "").replace("```sh", "").replace("```", "").strip()
            
        lines = terminal_text.split('\n')
        wrapped_lines = []
        for line in lines:
            if not line.strip():
                wrapped_lines.append("")
                continue
            wrapped_lines.extend(wrap_text(line, term_font, box_w - 40))
        
        text_y = box_y + 50
        for line in wrapped_lines:
            if line.strip().startswith("$") or line.strip().startswith(">"):
                draw.text((box_x + 20, text_y), line, font=term_font, fill="#4ADE80") # Green
            else:
                draw.text((box_x + 20, text_y), line, font=term_font, fill="#F1F5F9") # White
            text_y += 30
            if text_y > box_y + box_h - 40:
                break

def draw_concept_box(draw, width, height, concept_text, font):
    box_x = int(width * 0.55)
    box_y = int(height * 0.25)
    box_w = int(width * 0.4)
    box_h = int(height * 0.5)
    draw.rounded_rectangle([box_x-4, box_y-4, box_x + box_w+4, box_y + box_h+4], radius=20, fill="#38BDF8")
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=18, fill="#0F172A")
    draw.text((box_x + 30, box_y + 20), "Concept Analogy", font=font, fill="#38BDF8")
    draw.line([(box_x + 30, box_y + 70), (box_x + box_w - 30, box_y + 70)], fill="#334155", width=2)
    if concept_text:
        wrapped = wrap_text(str(concept_text), font, box_w - 60)
        text_y = box_y + 100
        for line in wrapped:
            draw.text((box_x + 30, text_y), line, font=font, fill="#F8FAFC")
            text_y += 45

def draw_mermaid_diagram(img, width, height, diagram_code):
    diagram_code = str(diagram_code).strip()
    if diagram_code.startswith("```mermaid"):
        diagram_code = diagram_code[10:]
    if diagram_code.endswith("```"):
        diagram_code = diagram_code[:-3]
    diagram_code = diagram_code.strip()

    compressed = zlib.compress(diagram_code.encode('utf-8'))
    encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
    url = f"https://kroki.io/mermaid/png/{encoded}"
    
    box_x = int(width * 0.55)
    box_y = int(height * 0.2)
    box_w = int(width * 0.4)
    box_h = int(height * 0.6)
    
    draw = ImageDraw.Draw(img)
    # Bright white background for the diagram
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=15, fill="#F8FAFC", outline="#38BDF8", width=4)
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            diagram_img = Image.open(io.BytesIO(response.read())).convert("RGBA")
            diagram_img.thumbnail((box_w - 40, box_h - 40), Image.Resampling.LANCZOS)
            paste_x = box_x + (box_w - diagram_img.width) // 2
            paste_y = box_y + (box_h - diagram_img.height) // 2
            img.paste(diagram_img, (paste_x, paste_y), diagram_img)
    except Exception as e:
        print(f"Failed to render mermaid diagram: {e}")
        font = get_font("Arial Unicode.ttf", 30)
        draw.text((box_x + 20, box_y + 20), "Diagram Error", fill="red", font=font)

def draw_background(draw, width, height):
    for y in range(height):
        ratio = y / height
        r = int(15 - 10 * ratio)
        g = int(23 - 8 * ratio)
        b = int(42 - 17 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    for x in range(0, width, 40):
        for y in range(0, height, 40):
            draw.rectangle([x, y, x+1, y+1], fill="#1E293B")


def draw_curriculum_map(img, width, height, visual_content):
    import json
    try:
        data = json.loads(visual_content)
    except Exception:
        data = {"past": [], "present": str(visual_content), "future": []}
    
    past = data.get("past", [])
    present = data.get("present", "")
    future = data.get("future", [])
    
    display_past = past[-2:]
    display_future = future[:4]
    
    items = []
    for p in display_past: items.append(("past", p))
    items.append(("present", present))
    for f in display_future: items.append(("future", f))
    
    draw = ImageDraw.Draw(img)
    
    box_x = int(width * 0.55)
    box_y = int(height * 0.2)
    box_w = int(width * 0.4)
    box_h = int(height * 0.6)
    
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=15, fill="#1E293B", outline="#334155", width=3)
    
    header_font = get_font("Arial Unicode.ttf", 30)
    draw.text((box_x + 30, box_y + 20), "Learning Path Timeline", font=header_font, fill="#A78BFA")
    draw.line([(box_x + 30, box_y + 70), (box_x + box_w - 30, box_y + 70)], fill="#334155", width=2)
    
    item_font = get_font("Arial Unicode.ttf", 28)
    bold_font = get_font("Arial Unicode.ttf", 32)
    
    y_offset = box_y + 100
    for state, text in items:
        lines = wrap_text(text, bold_font if state == "present" else item_font, box_w - 100)
        
        # Highlight background for present
        if state == "present":
            draw.rounded_rectangle([box_x + 60, y_offset - 5, box_x + box_w - 20, y_offset + len(lines)*40], radius=8, fill="#0F172A", outline="#38BDF8", width=2)
            
        for i, line in enumerate(lines):
            if i == 0:
                if state == "past":
                    draw.text((box_x + 30, y_offset), "✅", font=item_font, fill="#10B981")
                elif state == "present":
                    draw.text((box_x + 30, y_offset), "▶", font=bold_font, fill="#38BDF8")
                else:
                    draw.text((box_x + 30, y_offset), "○", font=item_font, fill="#64748B")
            
            if state == "past":
                draw.text((box_x + 70, y_offset), line, font=item_font, fill="#64748B")
            elif state == "present":
                draw.text((box_x + 70, y_offset), line, font=bold_font, fill="#38BDF8")
            else:
                draw.text((box_x + 70, y_offset), line, font=item_font, fill="#94A3B8")
                
            y_offset += 40
            
        y_offset += 20

def draw_title_slide(img, width, height, title, subtitle):
    draw = ImageDraw.Draw(img)
    
    # Fonts
    title_font = get_font("Arial Unicode.ttf", 110)
    subtitle_font = get_font("Arial Unicode.ttf", 55)
    
    left_margin = 100
    
    # 1. Draw large Title text
    title_y = int(height * 0.25)
    title_lines = wrap_text(str(title).upper(), title_font, int(width * 0.6))
    for line in title_lines:
        draw.text((left_margin, title_y), line, font=title_font, fill="#38BDF8")
        title_y += 120
        
    # Draw an elegant separator line
    line_y = title_y + 30
    draw.line([(left_margin, line_y), (left_margin + int(width * 0.5), line_y)], fill="#334155", width=4)
    
    # 2. Draw Subtitle text below the line
    subtitle_y = line_y + 60
    subtitle_lines = wrap_text(str(subtitle), subtitle_font, int(width * 0.6))
    for line in subtitle_lines:
        draw.text((left_margin, subtitle_y), line, font=subtitle_font, fill="#F8FAFC")
        subtitle_y += 70

def render_slide(title, content_text, visual_type, visual_content, output_base, output_content):

    width, height = 1920, 1080
    
    # 1. Base Image (Background + Title)
    base_img = Image.new("RGBA", (width, height), (0,0,0,255))
    base_draw = ImageDraw.Draw(base_img)
    draw_background(base_draw, width, height)
    
    bullet_font = get_font("Arial Unicode.ttf", 36)
    title_x, title_y = 100, 100
    
    if visual_type == "title_slide":
        # For the title slide, we just render the beautiful typography onto the base directly!
        draw_title_slide(base_img, width, height, title, content_text)
    else:
        title_font = get_font("Arial Unicode.ttf", 60)
        base_draw.text((title_x, title_y), title, font=title_font, fill="#38BDF8")
        base_draw.line([(title_x, title_y + 90), (width * 0.55, title_y + 90)], fill="#38BDF8", width=3)
    
    base_img.save(output_base)
    
    # 2. Content Image (Transparent background + Content Text + Visual Box)
    content_img = Image.new("RGBA", (width, height), (0,0,0,0))
    content_draw = ImageDraw.Draw(content_img)
    
    # Visuals
    if visual_type == "code_snippet":
        draw_code_block(content_draw, width, height, visual_content)
    elif visual_type == "concept_box":
        draw_concept_box(content_draw, width, height, visual_content, bullet_font)
    elif visual_type in ["architecture_diagram", "sequence_diagram"]:
        draw_mermaid_diagram(content_img, width, height, visual_content)
    elif visual_type == "curriculum_map":
        draw_curriculum_map(content_img, width, height, visual_content)
    elif visual_type == "terminal_output":
        draw_terminal_output(content_draw, width, height, visual_content)
        
    # Text
    if visual_type != "title_slide":
        content_y = 280
        max_text_width = (width * 0.55) - title_x
        if content_text:
            wrapped_lines = wrap_text(str(content_text), bullet_font, max_text_width)
            for line in wrapped_lines:
                content_draw.text((title_x, content_y), line, font=bullet_font, fill="#E2E8F0")
                content_y += 50
            
            
    content_img.save(output_content)

def generate_thumbnail(title, output_path, avatar_path="assets/masked_avatar_0.png"):
    width, height = 1280, 720
    img = Image.new("RGBA", (width, height), (0,0,0,255))
    draw = ImageDraw.Draw(img)
    draw_background(draw, width, height)
    
    # 1. Avatar (right side)
    if os.path.exists(avatar_path):
        with Image.open(avatar_path) as av:
            av = av.convert("RGBA")
            aspect = av.width / av.height
            new_h = 600
            new_w = int(new_h * aspect)
            av = av.resize((new_w, new_h), Image.Resampling.LANCZOS)
            img.paste(av, (width - new_w - 20, height - new_h), av)
            
    # 2. Text (left side)
    title_font = get_font("Arial Unicode.ttf", 80)
    badge_font = get_font("Arial Unicode.ttf", 40)
    
    # Draw badge
    draw.rounded_rectangle([80, 80, 420, 160], radius=15, fill="#38BDF8")
    draw.text((110, 95), "NEW LESSON", font=badge_font, fill="#0F172A")
    
    # Draw Title
    title_lines = wrap_text(str(title).upper(), title_font, 750)
    text_y = 220
    for line in title_lines:
        draw.text((84, text_y+4), line, font=title_font, fill="#000000") # shadow
        draw.text((80, text_y), line, font=title_font, fill="#F8FAFC")
        text_y += 90
        
    img.save(output_path)
