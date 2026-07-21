from app.services.spoof_detector import evaluate_spoofing

def test_evaluate_spoofing():
    # Simulating a low quality printed photo attack
    passive_scores = {"blur_score": 0.2, "texture_score": 0.2, "reflection_score": 1.0}
    result = evaluate_spoofing(passive_scores, {})
    
    assert result["lowest_score"] <= 0.5
    assert result["most_likely_attack"] == "printed_photo"
