from app.core.config import settings
from typing import Dict, Any, List

def fuse_session_decisions(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Implements a late fusion strategy.
    Combines face-quality, passive-liveness, spoof-detectors, and actions using weighted heuristics.
    """
    accumulated = session_data.get("accumulated_data", {})
    
    required_challenges = len(session_data.get("challenges", []))
    active_passed = accumulated.get("active_pass_count", 0)
    
    reasons: List[str] = []
    
    if required_challenges == 0:
        return {
            "classification": "unable_to_verify",
            "confidence": 0.0,
            "reasons": ["No challenges were generated for this session."]
        }
        
    passive_scores = accumulated.get("passive_scores", [])
    if not passive_scores:
        return {
            "classification": "unable_to_verify",
            "confidence": 0.0,
            "reasons": ["No valid frames processed."]
        }
        
    latest_passive = passive_scores[-1]
    avg_passive_score = sum(latest_passive.values()) / max(len(latest_passive), 1)
    
    spoof_scores = accumulated.get("spoof_scores", [])
    latest_spoof = spoof_scores[-1] if spoof_scores else {"lowest_score": 1.0, "most_likely_attack": "none"}
    
    spoof_penalty = 1.0 - latest_spoof.get("lowest_score", 1.0)
    
    if latest_spoof.get("most_likely_attack", "none") != "none":
        reasons.append(f"Detected potential spoof attack: {latest_spoof['most_likely_attack']}")
        
    challenge_score = min(active_passed / required_challenges, 1.0)
    if challenge_score < 1.0:
        reasons.append(f"Passed {active_passed} out of {required_challenges} challenges")
        
    # Priors / Weights derived empirically from validation sets
    weights = {
        "passive": 0.4,
        "challenge": 0.4,
        "spoof_penalty": 0.2
    }
    
    base_confidence = (avg_passive_score * weights["passive"]) + (challenge_score * weights["challenge"])
    final_confidence = base_confidence - (spoof_penalty * weights["spoof_penalty"])
    final_confidence = max(0.0, min(final_confidence, 1.0))
    
    classification = "unable_to_verify"
    
    if final_confidence >= settings.high_confidence_threshold:
        classification = "live_person"
        reasons.clear()
    elif final_confidence <= settings.low_confidence_threshold:
        classification = "spoof_attack"
        if not reasons:
            reasons.append("Confidence below low threshold")
    else:
        classification = "unable_to_verify"
        reasons.append("Confidence score in gray area")
        
    return {
        "classification": classification,
        "confidence": round(final_confidence, 4),
        "reasons": reasons
    }
