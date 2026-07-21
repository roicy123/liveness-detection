import cv2
import numpy as np
from typing import Dict, Any

def check_blur(image: np.ndarray) -> float:
    """
    Uses Laplacian variance to compute a focus measure (blurriness).
    Expects BGR image shape (H, W, 3).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Normalize (0 to 1). Higher is sharper. Cap at ~200.
    score = min(variance / 200.0, 1.0)
    return float(score)

def check_texture(image: np.ndarray) -> float:
    """
    Frequency-domain analysis via 2D FFT to identify moiré patterns or print artifact frequencies.
    Expects BGR image shape (H, W, 3).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1e-8)
    
    h, w = gray.shape
    cy, cx = h // 2, w // 2
    
    # Mask out the low frequencies
    mask_radius = int(min(h, w) * 0.1)
    y, x = np.ogrid[-cy:h-cy, -cx:w-cx]
    mask = x**2 + y**2 <= mask_radius**2
    magnitude_spectrum[mask] = 0
    
    valid_pixels = magnitude_spectrum[magnitude_spectrum > 0]
    if len(valid_pixels) == 0:
        return 0.0
        
    high_freq_energy = np.mean(valid_pixels)
    
    score = 1.0
    if np.isnan(high_freq_energy) or high_freq_energy < 50:
         score = 0.4 # suspicion of low detail/print
    elif high_freq_energy > 200:
         score = 0.3 # suspicious heavy peaks (Moiré)
    
    return float(score)

def check_reflection(image: np.ndarray, bbox: tuple) -> float:
    """Detect specular highlights common in screen glare."""
    x, y, w, h = [int(v) for v in bbox]
    face_roi = image[max(0, y):y+h, max(0, x):x+w]
    if face_roi.size == 0:
        return 1.0
        
    gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    bright_pixels = cv2.countNonZero(thresholded)
    total_pixels = gray.size
    
    bright_ratio = bright_pixels / (total_pixels + 1e-6)
    
    if bright_ratio > 0.05:
        return 0.1
    elif bright_ratio > 0.02:
        return 0.5
    return 1.0

def evaluate_passive_liveness(image: np.ndarray, face_data: Dict[str, Any]) -> Dict[str, float]:
    """Runs all passive liveness checks and returns individual scores."""
    return {
        "blur_score": check_blur(image),
        "texture_score": check_texture(image),
        "reflection_score": check_reflection(image, face_data["bbox"])
    }
