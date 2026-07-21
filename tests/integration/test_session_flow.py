from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_session_flow():
    resp = client.post("/api/v1/session") # Note: router usually mounted at root, let's check main.py...
    
    # Actually, in main.py it's api_router without prefix.
    # The routers in __init__.py have prefix="/session", so the path is /session
    resp = client.post("/session")
    assert resp.status_code == 200
    data = resp.json()
    session_id = data["session_id"]
    token = data["token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = client.get(f"/session/{session_id}/challenge", headers=headers)
    assert resp.status_code == 200
    challenges = resp.json()["challenges"]
    assert len(challenges) > 0
    
    resp = client.post(
        f"/session/{session_id}/finalize", 
        json={"nonce": "dummy-nonce-123"},
        headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["classification"] in ["live_person", "spoof_attack", "unable_to_verify"]
