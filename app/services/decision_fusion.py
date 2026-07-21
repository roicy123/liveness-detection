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
        
    total_passive_keys = passive_scores[0].keys()
    avg_passive_scores = {}
    for key in total_passive_keys:
        avg_passive_scores[key] = sum(s.get(key, 1.0) for s in passive_scores) / len(passive_scores)
    
    avg_passive_score = sum(avg_passive_scores.values()) / max(len(avg_passive_scores), 1)
    
    spoof_scores = accumulated.get("spoof_scores", [])
    worst_spoof = 1.0
    most_likely_attack = "none"
    if spoof_scores:
        worst_spoof = min(s.get("lowest_score", 1.0) for s in spoof_scores)
        for s in spoof_scores:
            if s.get("lowest_score", 1.0) == worst_spoof:
                most_likely_attack = s.get("most_likely_attack", "none")
                break
    
    spoof_penalty = 1.0 - worst_spoof
    
    if most_likely_attack != "none":
        reasons.append(f"Detected potential spoof attack: {most_likely_attack}")
        
    challenge_score = min(active_passed / required_challenges, 1.0)
    failed_challenges = session_data.get("failed_challenges", [])
    
    if challenge_score < 1.0:
        if failed_challenges:
            reasons.append(f"Failed challenge(s) (timed out): {', '.join(failed_challenges)}")
        else:
            reasons.append(f"Passed {active_passed} out of {required_challenges} challenges")
        
    # Priors / Weights derived empirically from validation sets
    weights = {
        "passive": 0.5,
        "challenge": 0.5,
        "spoof_penalty": 0.3
    }
    
    from app.utils.logging import audit_logger
    
    base_confidence = (avg_passive_score * weights["passive"]) + (challenge_score * weights["challenge"])
    final_confidence = base_confidence - (spoof_penalty * weights["spoof_penalty"])
    final_confidence = max(0.0, min(final_confidence, 1.0))
    
    audit_logger.debug("Decision Fusion Raw Math", extra={
        "avg_passive_score": avg_passive_score,
        "challenge_score": challenge_score,
        "spoof_penalty": spoof_penalty,
        "base_confidence": base_confidence,
        "final_confidence": final_confidence
    })
    
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
