import cv2
import numpy as np
from typing import Dict, Any, List, Tuple
from app.services.active_challenge import _calculate_ear

def check_blur(image: np.ndarray) -> float:
    """Uses Laplacian variance to compute a focus measure (blurriness)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    score = min(variance / 200.0, 1.0)
    return float(score)

def check_texture(image: np.ndarray) -> float:
    """Frequency-domain texture check to find moire patterns or print texture."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1e-8)
    
    h, w = gray.shape
    cy, cx = h // 2, w // 2
    
    mask_radius = int(min(h, w) * 0.1)
    y, x = np.ogrid[-cy:h-cy, -cx:w-cx]
    mask = x**2 + y**2 <= mask_radius**2
    magnitude_spectrum[mask] = 0
    
    valid_pixels = magnitude_spectrum[magnitude_spectrum > 0]
    if len(valid_pixels) == 0: return 0.0
        
    high_freq_energy = np.mean(valid_pixels)
    score = 1.0
    if np.isnan(high_freq_energy) or high_freq_energy < 50:
         score = 0.4
    elif high_freq_energy > 200:
         score = 0.3
    return float(score)

def check_reflection(image: np.ndarray, bbox: tuple) -> float:
    """Detect specular highlights common in screen glare."""
    x, y, w, h = [int(v) for v in bbox]
    face_roi = image[max(0, y):y+h, max(0, x):x+w]
    if face_roi.size == 0: return 1.0
        
    gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    bright_pixels = cv2.countNonZero(thresholded)
    total_pixels = gray.size
    
    bright_ratio = bright_pixels / (total_pixels + 1e-6)
    if bright_ratio > 0.05: return 0.1
    elif bright_ratio > 0.02: return 0.5
    return 1.0

def check_lighting_consistency(image: np.ndarray, session_data: Dict[str, Any]) -> float:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_lum = np.mean(gray)
    accumulated = session_data.setdefault("accumulated_data", {})
    if "lum_history" not in accumulated:
        accumulated["lum_history"] = []
    
    lum_history = accumulated["lum_history"]
    score = 1.0
    if len(lum_history) > 2:
        mean_past = np.mean(lum_history)
        std_past = np.std(lum_history)
        if std_past > 0 and abs(mean_lum - mean_past) > (2.5 * std_past):
            score = 0.1
    accumulated["lum_history"].append(mean_lum)
    return score

def check_natural_motion(landmarks: List[Tuple[float, float, float]], session_data: Dict[str, Any]) -> float:
    accumulated = session_data.setdefault("accumulated_data", {})
    if "centroid_history" not in accumulated:
        accumulated["centroid_history"] = []
    
    cx = sum(p[0] for p in landmarks) / len(landmarks)
    cy = sum(p[1] for p in landmarks) / len(landmarks)
    
    history = accumulated["centroid_history"]
    history.append((cx, cy))
    
    if len(history) < 5:
        return 1.0
        
    xs = [p[0] for p in history]
    ys = [p[1] for p in history]
    var_x = float(np.var(xs))
    var_y = float(np.var(ys))
    
    if var_x < 1e-6 and var_y < 1e-6:
        return 0.1
    return 1.0

def check_depth_cue(landmarks: List[Tuple[float, float, float]]) -> float:
    zs = [p[2] for p in landmarks]
    variance = float(np.var(zs))
    if variance < 1e-5:
        return 0.1
    elif variance < 1e-4:
        return 0.5
    return 1.0

def track_passive_blink(landmarks: List[Tuple[float, float, float]], session_data: Dict[str, Any]) -> float:
    ear = _calculate_ear(landmarks)
    accumulated = session_data.setdefault("accumulated_data", {})
    passive_ear_history = accumulated.setdefault("passive_ear_history", [])
    passive_ear_history.append(ear)
    
    if len(passive_ear_history) >= 10:
        min_ear = min(passive_ear_history[-30:])
        max_ear = max(passive_ear_history[-30:])
        if min_ear < 0.22 and max_ear > 0.28:
            accumulated["passive_blink_detected"] = True
            
    return 1.0 if accumulated.get("passive_blink_detected", False) else 0.5

def evaluate_passive_liveness(image: np.ndarray, face_data: Dict[str, Any], session_data: Dict[str, Any]) -> Dict[str, float]:
    landmarks = face_data["landmarks"]
    return {
        "blur_score": check_blur(image),
        "texture_score": check_texture(image),
        "reflection_score": check_reflection(image, face_data["bbox"]),
        "lighting_consistency_score": check_lighting_consistency(image, session_data),
        "natural_motion_score": check_natural_motion(landmarks, session_data),
        "depth_cue_score": check_depth_cue(landmarks),
        "passive_blink_score": track_passive_blink(landmarks, session_data)
    }
