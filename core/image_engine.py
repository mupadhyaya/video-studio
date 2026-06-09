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

def render_slide(title, content_bullets, output_path):
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
    draw.line([(title_x, title_y + 90), (width - title_x, title_y + 90)], fill="#38BDF8", width=3)
    
    # Draw bullet points
    content_y = 280
    max_text_width = width - (title_x * 2) - 40 # padding
    
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
