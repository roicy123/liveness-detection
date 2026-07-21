import math
import random
from typing import List, Tuple, Dict, Any
from app.utils.logging import audit_logger

CHALLENGE_POOL = [
    "blink", "smile", "turn_left", "turn_right", 
    "look_up", "look_down", "open_mouth", "raise_eyebrows"
]

def generate_challenges(count: int = 3) -> List[str]:
    return random.sample(CHALLENGE_POOL, min(count, len(CHALLENGE_POOL)))

def _distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def _get_face_width(landmarks: List[Tuple[float, float, float]]) -> float:
    return _distance(landmarks[234], landmarks[454])

def _get_face_height(landmarks: List[Tuple[float, float, float]]) -> float:
    return _distance(landmarks[10], landmarks[152])

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
    ear_history = ear_history[-30:] # Rolling 30 frames
    accumulated["ear_history"] = ear_history
    
    if len(ear_history) < 3: return 0.0
        
    min_ear = min(ear_history)
    max_ear = max(ear_history)
    
    if max_ear == 0: return 0.0
    drop_ratio = (max_ear - min_ear) / max_ear
    
    audit_logger.debug("Blink baseline logic", extra={
        "min_ear": min_ear, 
        "max_ear": max_ear, 
        "drop_ratio": drop_ratio
    })
    
    if drop_ratio > 0.35:
        return 1.0  
    return 0.0

def check_smile(landmarks: List[Tuple[float, float, float]], session_data: Dict[str, Any]) -> float:
    w = _distance(landmarks[61], landmarks[291])
    face_w = _get_face_width(landmarks)
    if face_w == 0: return 0.0
    val = w / face_w
    
    accumulated = session_data.setdefault("accumulated_data", {})
    baseline = accumulated.setdefault("baseline_smile", val)
    
    delta = val - baseline
    
    audit_logger.debug("Smile baseline logic", extra={
        "current_val": val, 
        "baseline": baseline, 
        "delta": delta
    })
    
    if delta > 0.04:
        return 1.0
    return 0.0

def check_open_mouth(landmarks: List[Tuple[float, float, float]], session_data: Dict[str, Any]) -> float:
    mouth_h = _distance(landmarks[13], landmarks[14])
    face_h = _get_face_height(landmarks)
    if face_h == 0: return 0.0
    val = mouth_h / face_h
    
    accumulated = session_data.setdefault("accumulated_data", {})
    baseline = accumulated.setdefault("baseline_mouth", val)
    delta = val - baseline
    
    audit_logger.debug("Open mouth baseline logic", extra={
        "current_val": val, 
        "baseline": baseline, 
        "delta": delta
    })
    
    if delta > 0.025:
        return 1.0
    return 0.0

def check_head_turn(landmarks: List[Tuple[float, float, float]], direction: str, session_data: Dict[str, Any]) -> float:
    nose = landmarks[1]
    
    accumulated = session_data.setdefault("accumulated_data", {})
    score = 0.0
    
    if direction in ["turn_right", "turn_left"]:
        face_width = _get_face_width(landmarks)
        if face_width == 0: return 0.0
        
        baseline_nose_x = accumulated.setdefault("baseline_nose_x", nose[0])
        normalized_shift = (nose[0] - baseline_nose_x) / face_width
        
        audit_logger.debug("Head Turn baseline logic", extra={
            "direction": direction,
            "nose_x": nose[0],
            "baseline_nose_x": baseline_nose_x,
            "normalized_shift": normalized_shift
        })
        
        if direction == "turn_right":
            if normalized_shift > 0.08: score = 1.0 
        elif direction == "turn_left":
            if normalized_shift < -0.08: score = 1.0  
            
    elif direction in ["look_up", "look_down"]:
        left_eye = landmarks[33]
        right_eye = landmarks[263]
        face_h = _get_face_height(landmarks)
        if face_h == 0: return 0.0
        
        pitch_val = (nose[1] - (left_eye[1] + right_eye[1])/2) / face_h
        baseline_pitch = accumulated.setdefault("baseline_pitch", pitch_val)
        delta = pitch_val - baseline_pitch
        
        audit_logger.debug("Head Pitch baseline logic", extra={
            "direction": direction,
            "pitch_val": pitch_val,
            "baseline_pitch": baseline_pitch,
            "delta": delta
        })
        
        if direction == "look_up":
            if delta < -0.035: score = 1.0
        elif direction == "look_down":
            if delta > 0.035: score = 1.0
            
    return score

def check_raise_eyebrows(landmarks: List[Tuple[float, float, float]], session_data: Dict[str, Any]) -> float:
    curr_dist = _distance(landmarks[105], landmarks[159]) 
    face_h = _get_face_height(landmarks)
    if face_h == 0: return 0.0
    norm_dist = curr_dist / face_h
    
    accumulated = session_data.setdefault("accumulated_data", {})
    baseline = accumulated.setdefault("baseline_eyebrow", norm_dist)
    delta = norm_dist - baseline
    
    audit_logger.debug("Raise eyebrows baseline logic", extra={
        "curr_dist": norm_dist, 
        "baseline": baseline, 
        "delta": delta
    })
    
    if delta > 0.006: 
        return 1.0
    return 0.0
