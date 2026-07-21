from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)

def _get_base_headers():
    resp = client.post("/session")
    assert resp.status_code == 200
    token = resp.json()["token"]
    session_id = resp.json()["session_id"]
    return session_id, {"Authorization": f"Bearer {token}"}

def test_full_session_flow():
    session_id, headers = _get_base_headers()
    
    resp = client.get(f"/session/{session_id}/challenge", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["challenges"]) > 0
    
    resp = client.post(
        f"/session/{session_id}/finalize", 
        json={"nonce": "dummy-nonce-123"},
        headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["classification"] in ["live_person", "spoof_attack", "unable_to_verify"]

def test_reused_nonce():
    session_id, headers = _get_base_headers()
    client.get(f"/session/{session_id}/challenge", headers=headers)
    
    payload = {"nonce": "same-nonce"}
    res1 = client.post(f"/session/{session_id}/finalize", json=payload, headers=headers)
    assert res1.status_code == 200
    
    res2 = client.post(f"/session/{session_id}/finalize", json=payload, headers=headers)
    assert res2.status_code == 422
    assert "Nonce" in res2.json()["detail"]

def test_expired_session(monkeypatch):
    import app.core.config
    monkeypatch.setattr(app.core.config.settings, "session_timeout_seconds", 0)
    
    resp = client.post("/session")
    token = resp.json()["token"]
    session_id = resp.json()["session_id"]
    headers = {"Authorization": f"Bearer {token}"}
    
    time.sleep(0.1) # allow expiration
    # Challenge GET should fail since token expired instantly, catching via PyJWT and returning 401
    res = client.get(f"/session/{session_id}/challenge", headers=headers)
    assert res.status_code == 401

def test_failure_injection_graceful_eval(monkeypatch):
    session_id, headers = _get_base_headers()
    client.get(f"/session/{session_id}/challenge", headers=headers)
    
    def mock_fuse(*args, **kwargs):
        raise RuntimeError("Injected heavy failure")
        
    import app.api.routes.verify
    monkeypatch.setattr(app.api.routes.verify, "fuse_session_decisions", mock_fuse)
    
    payload = {"nonce": "dummy-fail-123"}
    res = client.post(f"/session/{session_id}/finalize", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["classification"] == "unable_to_verify"
    assert "pipeline failed" in res.json()["reasons"][0]

def test_challenge_timeout(monkeypatch):
    import time
    import app.api.routes.verify
    
    session_id, headers = _get_base_headers()
    client.get(f"/session/{session_id}/challenge", headers=headers)
    
    original_time = time.time
    monkeypatch.setattr(time, "time", lambda: original_time() + 15.0)
    
    # Mock heavy image components so we hit the logic cleanly
    monkeypatch.setattr(app.api.routes.verify, "base64_to_image", lambda x: "img")
    monkeypatch.setattr(app.api.routes.verify, "strip_exif", lambda x: "img")
    monkeypatch.setattr(app.api.routes.verify, "detect_face", lambda x: {"landmarks": [], "bbox": (0,0,0,0)})
    monkeypatch.setattr(app.api.routes.verify, "evaluate_passive_liveness", lambda *args: {})
    monkeypatch.setattr(app.api.routes.verify, "evaluate_spoofing", lambda *args: {})
    
    payload = {
        "nonce": "timeout-nonce",
        "image_base64": "dummy"
    }
    
    res = client.post(f"/session/{session_id}/frame", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "rejected"
    assert res.json()["rejected_reason"] == "Challenge timed out"
