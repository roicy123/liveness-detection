from typing import Dict, Any, Tuple

def detect_printed_photo(passive_scores: Dict[str, float]) -> Tuple[float, str]:
    score = (passive_scores.get("texture_score", 1.0) + passive_scores.get("blur_score", 1.0)) / 2.0
    return score, "printed_photo"

def detect_screen_replay(passive_scores: Dict[str, float]) -> Tuple[float, str]:
    score = (passive_scores.get("reflection_score", 1.0) + passive_scores.get("texture_score", 1.0)) / 2.0
    return score, "screen_replay"

def detect_static_image(session_data: Dict[str, Any]) -> Tuple[float, str]:
    accumulated = session_data.get("accumulated_data", {})
    passive_scores = accumulated.get("passive_scores", [])
    if passive_scores:
        latest = passive_scores[-1]
        return latest.get("natural_motion_score", 1.0), "static_image"
    return 1.0, "static_image"

def detect_deepfake(image_data: Any) -> Tuple[float, str]:
    # Extension stub for 2D classification (e.g. EfficientNet)
    return 1.0, "deepfake"

def detect_ai_generated(image_data: Any) -> Tuple[float, str]:
    # Extension stub for StyleGAN/Diffusion tracking
    return 1.0, "ai_generated_face"

def detect_mask(image_data: Any) -> Tuple[float, str]:
    # Extension stub for 3D depth/multispectral
    return 1.0, "3d_mask"

def evaluate_spoofing(passive_scores: Dict[str, float], session_data: Dict[str, Any]) -> Dict[str, Any]:
    detectors = [
        detect_printed_photo(passive_scores),
        detect_screen_replay(passive_scores),
        detect_static_image(session_data),
        detect_deepfake(None),
        detect_ai_generated(None),
        detect_mask(None)
    ]
    
    results = {}
    for score, attack_type in detectors:
        results[attack_type] = score
        
    min_score = min(score for score, _ in detectors)
    most_likely_attack = [attack for score, attack in detectors if score == min_score][0]

    return {
        "scores": results,
        "lowest_score": min_score,
        "most_likely_attack": most_likely_attack if min_score < 0.5 else "none"
    }
