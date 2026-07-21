from typing import Dict, Any, Tuple

def detect_printed_photo(passive_scores: Dict[str, float]) -> Tuple[float, str]:
    """Score logic based on texture and blur for print attack."""
    score = (passive_scores.get("texture_score", 1.0) + passive_scores.get("blur_score", 1.0)) / 2.0
    return score, "printed_photo"

def detect_screen_replay(passive_scores: Dict[str, float]) -> Tuple[float, str]:
    """Score logic based on reflection and texture for screen replay."""
    score = (passive_scores.get("reflection_score", 1.0) + passive_scores.get("texture_score", 1.0)) / 2.0
    return score, "screen_replay"

def detect_static_image(session_data: Dict[str, Any]) -> Tuple[float, str]:
    """Check if motion/challenges were too static across frames."""
    # TODO: Analyze variance of landmarks across accumulated frames.
    return 1.0, "static_image"

def detect_deepfake(image_data: Any) -> Tuple[float, str]:
    """
    Extension point for deepfake detection.
    Would typically use an ONNX model (e.g., EfficientNet trained on FaceForensics++).
    """
    return 1.0, "deepfake"

def detect_ai_generated(image_data: Any) -> Tuple[float, str]:
    """
    Extension point for AI-generated face (StyleGAN/diffusion) detection.
    """
    return 1.0, "ai_generated_face"

def detect_mask(image_data: Any) -> Tuple[float, str]:
    """
    Extension point for 3D silicone mask detection.
    Can use depth maps if available, or specialized multispectral capture.
    """
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
