import cv2
import numpy as np
import os

def generate_synthetic_fixtures():
    fixtures_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Blank textureless image
    blank = np.ones((480, 640, 3), dtype=np.uint8) * 128
    cv2.imwrite(os.path.join(fixtures_dir, "synthetic_flat.jpg"), blank)
    
    # 2. Moire pattern image to test texture validation
    y, x = np.ogrid[0:480, 0:640]
    freq = (x*x + y*y) / 20.0
    moire = (np.sin(freq) * 127 + 128).astype(np.uint8)
    moire_rgb = cv2.cvtColor(moire, cv2.COLOR_GRAY2BGR)
    cv2.imwrite(os.path.join(fixtures_dir, "synthetic_moire.jpg"), moire_rgb)
    
    # 3. Bright glare image
    glare = np.ones((480, 640, 3), dtype=np.uint8) * 50
    # Add a huge white circle in the middle
    cv2.circle(glare, (320, 240), 150, (255, 255, 255), -1)
    cv2.imwrite(os.path.join(fixtures_dir, "synthetic_glare.jpg"), glare)
    
    # Generate labels.json
    import json
    labels = {
        "synthetic_flat.jpg": "spoof_attack",
        "synthetic_moire.jpg": "spoof_attack",
        "synthetic_glare.jpg": "spoof_attack"
    }
    with open(os.path.join(fixtures_dir, "labels.json"), "w") as f:
        json.dump(labels, f, indent=4)
        
if __name__ == "__main__":
    generate_synthetic_fixtures()
    print("Synthetic fixtures generated.")
