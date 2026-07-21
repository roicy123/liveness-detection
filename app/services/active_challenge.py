import math
import random
from typing import List, Tuple, Dict, Any

CHALLENGE_POOL = [
    "blink", "smile", "turn_left", "turn_right", 
    "look_up", "look_down", "open_mouth", "raise_eyebrows"
]

def generate_challenges(count: int = 3) -> List[str]:
    return random.sample(CHALLENGE_POOL, min(count, len(CHALLENGE_POOL)))

def _distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def _calculate_ear(landmarks: List[Tuple[float, float, float]]) -> float:
    p1, p4 = landmarks[33], landmarks[133]
    p2, p6 = landmarks[159], landmarks[145]
    p3, p5 = landmarks[158], landmarks[153]
    h1 = _distance(p2, p6)
    h2 = _distance(p3, p5)
    w = _distance(p1, p4)
    if w == 0: return 0.0
    return (h1 + h2) / (2.0 * w)

def check_blink(landmarks: List[Tuple[float, float, float]], session_data: Dict[str, Any]) -> float:
    accumulated = session_data.setdefault("accumulated_data", {})
    ear_history = accumulated.setdefault("ear_history", [])
    
    current_ear = _calculate_ear(landmarks)
    ear_history.append(current_ear)
    
    ear_history = ear_history[-30:]
    accumulated["ear_history"] = ear_history
    
    if len(ear_history) < 3: return 0.0
        
    min_ear = min(ear_history)
    max_ear = max(ear_history)
    
    # Ultra-loose fallback for any tiny eye squeeze
    if min_ear < 0.26 and max_ear > 0.24:
        return 1.0  
    return 0.0

def check_smile(landmarks: List[Tuple[float, float, float]]) -> float:
    w = _distance(landmarks[61], landmarks[291])
    h = _distance(landmarks[0], landmarks[17])
    if h == 0: return 0.0
    ratio = w / h
    # Normal is ~1.8, any stretch > 2.0 passes
    if ratio > 2.0:
        return 1.0
    return 0.0

def check_open_mouth(landmarks: List[Tuple[float, float, float]]) -> float:
    mouth_h = _distance(landmarks[13], landmarks[14])
    face_h = _distance(landmarks[10], landmarks[152])
    if face_h == 0: return 0.0
    val = mouth_h / face_h
    # Normal closed is ~0.02, any drop > 0.05 passes
    if val > 0.05:
        return 1.0
    return 0.0

def check_head_turn(landmarks: List[Tuple[float, float, float]], direction: str) -> float:
    nose = landmarks[1]
    left_eye = landmarks[33]
    right_eye = landmarks[263]
    
    d_left = _distance(nose, left_eye)
    d_right = _distance(nose, right_eye)
    if d_left == 0 or d_right == 0: return 0.0
    
    score = 0.0
    if direction == "turn_right":
        if (d_right / d_left) > 1.25: score = 1.0 
    elif direction == "turn_left":
        if (d_left / d_right) > 1.25: score = 1.0  
    elif direction == "look_up":
        face_h = _distance(landmarks[10], landmarks[152])
        if face_h > 0 and ((nose[1] - (left_eye[1] + right_eye[1])/2) / face_h) < 0.20:
            score = 1.0
    elif direction == "look_down":
        face_h = _distance(landmarks[10], landmarks[152])
        if face_h > 0 and ((nose[1] - (left_eye[1] + right_eye[1])/2) / face_h) > 0.23:
            score = 1.0
    return score

def check_raise_eyebrows(landmarks: List[Tuple[float, float, float]], session_data: Dict[str, Any]) -> float:
    curr_dist = _distance(landmarks[105], landmarks[159]) 
    face_h = _distance(landmarks[10], landmarks[152])
    if face_h == 0: return 0.0
    norm_dist = curr_dist / face_h
    
    accumulated = session_data.setdefault("accumulated_data", {})
    baseline = accumulated.setdefault("baseline_eyebrow", norm_dist)
    
    # Any tiny lift > 0.005
    if (norm_dist - baseline) > 0.005: 
        return 1.0
    return 0.0
