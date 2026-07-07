from moviepy import VideoClip
import numpy as np

def make_typewriter_mask(t, duration, width, height, num_lines=15):
    progress = min(1.0, t / (duration * 0.8)) # finish typing at 80%
    mask = np.zeros((height, width), dtype=float)
    
    current_line = int(progress * num_lines)
    if current_line > 0:
        line_height = height // num_lines
        mask[:current_line * line_height, :] = 1.0
        
    if current_line < num_lines:
        line_progress = (progress * num_lines) - current_line
        line_height = height // num_lines
        current_width = int(line_progress * width)
        mask[current_line * line_height : (current_line + 1) * line_height, :current_width] = 1.0
        
    return mask

# Test it
mask = make_typewriter_mask(1.0, 2.0, 100, 100)
print(mask.shape, mask.max())
