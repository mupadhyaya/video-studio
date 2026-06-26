import cv2
import numpy as np
from PIL import Image

def align_image(base_bgr, target_bgr):
    # Convert to grayscale for template matching
    base_gray = cv2.cvtColor(base_bgr, cv2.COLOR_BGR2GRAY)
    target_gray = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2GRAY)
    
    # We want to align based on the upper face (eyes/nose)
    # Let's extract a template patch from the upper middle
    h, w = base_gray.shape
    template_w = int(w * 0.4)
    template_h = int(h * 0.3)
    x_start = (w - template_w) // 2
    y_start = int(h * 0.1) # Upper face
    
    template = base_gray[y_start:y_start+template_h, x_start:x_start+template_w]
    
    # Match template
    res = cv2.matchTemplate(target_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    dx = x_start - max_loc[0]
    dy = y_start - max_loc[1]
    
    print(f"Shift required: dx={dx}, dy={dy} (Confidence: {max_val:.3f})")
    
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    aligned = cv2.warpAffine(target_bgr, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
    return aligned

def compose_avatars():
    print("Loading HINDI grid to create perfectly stable masked mouth images...")
    
    grid_path = "assets/MASTER_HINDI_AVATAR_6VISEME_GRID.png"
    img = Image.open(grid_path).convert("RGBA")
    
    frame_w = img.width // 3
    frame_h = img.height // 2
    
    viseme_mapping_hi = {
        "hindi_rest": (0, 0),
        "hindi_bmp":  (0, 1),
        "hindi_aa":   (0, 2),
        "hindi_oh":   (1, 0),
        "hindi_ee":   (1, 1),
        "hindi_ai":   (1, 2)
    }
    
    crops = {}
    for name, (row, col) in viseme_mapping_hi.items():
        left = col * frame_w
        upper = row * frame_h
        right = left + frame_w
        lower = upper + frame_h
        crops[name] = np.array(img.crop((left, upper, right, lower)))
    
    base_img = cv2.cvtColor(crops["hindi_rest"], cv2.COLOR_RGBA2BGRA)
    
    # Load Haar cascades
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
    
    gray = cv2.cvtColor(base_img[:,:,:3], cv2.COLOR_BGR2GRAY)
    
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    if len(faces) == 0:
        print("No face found by cascade classifier!")
        # Fallback full box
        faces = [[int(frame_w * 0.2), int(frame_h * 0.1), int(frame_w * 0.6), int(frame_h * 0.6)]]
        
    (fx, fy, fw, fh) = faces[0]
    print(f"Detected face: {fx}, {fy}, {fw}, {fh}")
    
    roi_gray = gray[fy + int(fh/2):fy+fh, fx:fx+fw]
    smiles = smile_cascade.detectMultiScale(roi_gray, 1.8, 20)
    
    if len(smiles) > 0:
        (sx, sy, sw, sh) = smiles[0]
        mx = fx + sx
        my = fy + int(fh/2) + sy
        mw = sw
        mh = sh
        print(f"Detected mouth: {mx}, {my}, {mw}, {mh}")
    else:
        print("No mouth found by cascade! Using geometric assumption.")
        mw = int(fw * 0.5)
        mh = int(fh * 0.25)
        mx = fx + int(fw * 0.25)
        my = fy + int(fh * 0.7)
    
    # Create soft feathered mask
    pad_x = int(mw * 0.5)
    pad_y = int(mh * 0.5)
    
    img_h, img_w = base_img.shape[:2]
    
    x1 = max(0, mx - pad_x)
    y1 = max(0, my - pad_y)
    x2 = min(img_w, mx + mw + pad_x)
    y2 = min(img_h, my + mh + pad_y)
    
    mask = np.zeros((img_h, img_w), dtype=np.uint8)
    cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
    
    blur_amount = max(mw, mh)
    if blur_amount % 2 == 0:
        blur_amount += 1
    mask = cv2.GaussianBlur(mask, (blur_amount, blur_amount), 0)
    
    mask_3c = cv2.merge([mask, mask, mask])
    mask_float = mask_3c.astype(float) / 255.0
    
    base_float = base_img.astype(float)
    
    for name, crop_arr in crops.items():
        if name == "hindi_rest":
            cv2.imwrite(f"assets/masked_{name}.png", base_img)
            continue
            
        target_img = cv2.cvtColor(crop_arr, cv2.COLOR_RGBA2BGRA)
        
        # ALIGN the target image to the base image BEFORE masking!
        print(f"Aligning {name}...")
        aligned_target = align_image(base_img, target_img)
        target_float = aligned_target.astype(float)
        
        blended_bgr = base_float[:,:,:3] * (1 - mask_float) + target_float[:,:,:3] * mask_float
        
        result = np.zeros_like(base_img)
        result[:,:,:3] = blended_bgr.astype(np.uint8)
        result[:,:,3] = base_img[:,:,3]
        
        cv2.imwrite(f"assets/masked_{name}.png", result)
        print(f"Composited assets/masked_{name}.png")

if __name__ == "__main__":
    compose_avatars()
