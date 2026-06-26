import cv2
import numpy as np

def compose_avatars():
    print("Loading aligned avatars...")
    base_img = cv2.imread("assets/aligned_avatar_0.png", cv2.IMREAD_UNCHANGED)
    
    # Load Haar cascades
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
    
    gray = cv2.cvtColor(base_img[:,:,:3], cv2.COLOR_BGR2GRAY)
    
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    if len(faces) == 0:
        print("No face found by cascade classifier!")
        return
        
    (fx, fy, fw, fh) = faces[0]
    print(f"Detected face: {fx}, {fy}, {fw}, {fh}")
    
    # The mouth is in the lower half of the face bounding box
    roi_gray = gray[fy + int(fh/2):fy+fh, fx:fx+fw]
    
    # Detect smile/mouth
    smiles = smile_cascade.detectMultiScale(roi_gray, 1.8, 20)
    
    if len(smiles) > 0:
        (sx, sy, sw, sh) = smiles[0]
        # Coordinates relative to whole image
        mx = fx + sx
        my = fy + int(fh/2) + sy
        mw = sw
        mh = sh
        print(f"Detected mouth: {mx}, {my}, {mw}, {mh}")
    else:
        print("No mouth found by cascade! Using geometric assumption.")
        # If cascade fails, geometrically guess the mouth location inside the face
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
    
    cv2.imwrite("assets/masked_avatar_0.png", base_img)
    base_float = base_img.astype(float)
    
    for i in range(1, 4):
        target_img = cv2.imread(f"assets/aligned_avatar_{i}.png", cv2.IMREAD_UNCHANGED)
        target_float = target_img.astype(float)
        
        blended_bgr = base_float[:,:,:3] * (1 - mask_float) + target_float[:,:,:3] * mask_float
        
        result = np.zeros_like(base_img)
        result[:,:,:3] = blended_bgr.astype(np.uint8)
        result[:,:,3] = base_img[:,:,3]
        
        cv2.imwrite(f"assets/masked_avatar_{i}.png", result)
        print(f"Composited masked_avatar_{i}.png")

if __name__ == "__main__":
    compose_avatars()
