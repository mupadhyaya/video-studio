import os
from PIL import Image, ImageDraw, ImageFont

def get_font(font_name="Arial.ttf", size=36):
    """
    Attempts to load a TrueType font from standard macOS paths, falling back to 
    ImageFont.load_default() if not found.
    """
    font_paths = [
        f"/System/Library/Fonts/Supplemental/{font_name}",
        f"/Library/Fonts/{font_name}",
        f"/System/Library/Fonts/{font_name}",
        # Fallbacks for other platforms just in case
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        f"/usr/share/fonts/TTF/{font_name}"
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    
    # Fallback to default PIL font
    return ImageFont.load_default()

def wrap_text(text, font, max_width):
    """
    Wraps text to fit within a maximum width in pixels.
    """
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        
        # Determine width of test line
        try:
            # Pillow >= 10.0.0
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]
        except AttributeError:
            # Pillow < 10.0.0 fallback
            width, _ = font.getsize(test_line)
            
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                # Word itself is too long, force wrap
                lines.append(word)
                
    if current_line:
        lines.append(" ".join(current_line))
        
    return lines

import math
import random

def draw_geometric_art(draw, width, height, prompt):
    """
    Draws abstract geometric art on the right side of the slide based on keywords.
    """
    # Define a bounding box for the art (right 40% of the screen)
    art_x_start = int(width * 0.6)
    art_y_start = int(height * 0.2)
    art_w = int(width * 0.35)
    art_h = int(height * 0.6)
    center_x = art_x_start + (art_w // 2)
    center_y = art_y_start + (art_h // 2)

    prompt = str(prompt).lower()
    
    # Base styling
    colors = ["#38BDF8", "#818CF8", "#C084FC", "#F472B6", "#94A3B8"]
    
    if "network" in prompt or "node" in prompt or "graph" in prompt:
        # Draw a network graph
        nodes = []
        for _ in range(12):
            nx = random.randint(art_x_start, art_x_start + art_w)
            ny = random.randint(art_y_start, art_y_start + art_h)
            nodes.append((nx, ny))
            
        # Draw edges
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                if random.random() > 0.6: # 40% chance of connection
                    draw.line([nodes[i], nodes[j]], fill="#1E293B", width=2)
                    
        # Draw nodes
        for nx, ny in nodes:
            r = random.randint(8, 20)
            draw.ellipse([nx-r, ny-r, nx+r, ny+r], fill=random.choice(colors), outline="#F8FAFC", width=2)
            
    elif "database" in prompt or "cylinder" in prompt or "store" in prompt:
        # Draw floating database cylinders
        for i in range(3):
            dx = center_x - 100 + (i * 80)
            dy = center_y - 150 + (i * 50)
            cw, ch = 120, 160
            color = random.choice(colors[:3])
            # Draw cylinder body
            draw.rectangle([dx, dy, dx+cw, dy+ch], fill=color)
            # Draw bottom ellipse
            draw.ellipse([dx, dy+ch-20, dx+cw, dy+ch+20], fill=color)
            # Draw top ellipse (lid)
            draw.ellipse([dx, dy-20, dx+cw, dy+20], fill="#F8FAFC", outline=color, width=3)
            
    else:
        # Default abstract geometric composition
        for _ in range(8):
            shape_type = random.choice(["circle", "rect", "line"])
            color = random.choice(colors)
            sx = random.randint(art_x_start, art_x_start + art_w - 100)
            sy = random.randint(art_y_start, art_y_start + art_h - 100)
            sr = random.randint(40, 120)
            
            if shape_type == "circle":
                draw.ellipse([sx, sy, sx+sr, sy+sr], outline=color, width=6)
            elif shape_type == "rect":
                draw.rectangle([sx, sy, sx+sr, sy+sr], outline=color, width=4)
            else:
                draw.line([(sx, sy), (sx+sr, sy+sr)], fill=color, width=8)

def render_slide(title, content_bullets, image_prompt, output_path):
    """
    Renders a landscape slide frame (1920x1080) using the specified color palette.
    - Background: Slate (#0F172A)
    - Title: Blue (#38BDF8)
    - Content: White (#E2E8F0)
    """
    # Create canvas
    width, height = 1920, 1080
    bg_color = "#0F172A"
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    title_font = get_font("Helvetica.ttc", 60)
    if isinstance(title_font, ImageFont.ImageFont): # If fallback default font is loaded, size is ignored
        pass
    else:
        # Re-try Arial if Helvetica isn't standard font format
        title_font = get_font("Arial.ttf", 60)
        
    bullet_font = get_font("Arial.ttf", 36)
    
    # Draw Title
    title_x = 100
    title_y = 100
    draw.text((title_x, title_y), title, font=title_font, fill="#38BDF8")
    
    # Draw horizontal divider line under title
    draw.line([(title_x, title_y + 90), (width * 0.55, title_y + 90)], fill="#38BDF8", width=3)
    
    # Draw Geometric Art on the right 40%
    if image_prompt:
        draw_geometric_art(draw, width, height, image_prompt)
    
    # Draw bullet points (Constrain width to 55%)
    content_y = 280
    max_text_width = (width * 0.55) - title_x
    
    for bullet in content_bullets:
        wrapped_lines = wrap_text(bullet, bullet_font, max_text_width)
        
        for idx, line in enumerate(wrapped_lines):
            if idx == 0:
                # Draw the bullet symbol and first line
                draw.text((title_x + 20, content_y), "•", font=bullet_font, fill="#38BDF8")
                draw.text((title_x + 60, content_y), line, font=bullet_font, fill="#E2E8F0")
            else:
                # Draw subsequent wrapped lines indented
                draw.text((title_x + 60, content_y), line, font=bullet_font, fill="#E2E8F0")
            
            # Line spacing
            content_y += 50
            
        # Bullet spacing
        content_y += 30
        
    # Save frame
    img.save(output_path)
