# Liveness Detection API

A production-quality REST-API for facial liveness detection, combining passive liveness (OpenCV) and active challenge response verification (MediaPipe).

## Setup

```bash
docker-compose up --build
```
Alternatively, for local dev without Docker:
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Architecture Summary
The system is built as a FastAPI service that relies on stateless endpoints coordinated via Redis (with an in-memory fallback). Frame-by-frame analysis pipelines sequentially trigger: `Face Detection` (MediaPipe Face Mesh), partial `Passive Liveness` (Texture/Blur), and `Active Challenge` completion tracking. The final classification fuses these scores via `Spoof Detector` checks and dynamic thresholding in the `Decision Fusion` engine.

## Modular Structure
- `app/api/`: Request routing and schemas.
- `app/services/face_detector.py`: Single-face bounds and landmarks check via MediaPipe.
- `app/services/passive_liveness.py`: CV-based blur/glare rules without CNN payload.
- `app/services/active_challenge.py`: Gesture generation and sequencing.
- `app/services/spoof_detector.py`: Scoring against Print/Screen replay.
- `app/services/decision_fusion.py`: Rule-based thresholding for finalizing results.
- `tests/`: Integration and unit tests per pipeline node.

## Usage Example
```python
import requests

base_url = "http://localhost:8000"

# 1. Start Session
s = requests.post(f"{base_url}/session").json()
session_id = s["session_id"]
headers = {"Authorization": f"Bearer {s['token']}"}

# 2. Get Challenge
chal = requests.get(f"{base_url}/session/{session_id}/challenge", headers=headers).json()
print("Challenges:", chal)

# 3. Submit Frame (Tiny 1x1 base64 GIF/PNG representation)
frame_data = {"nonce": "1", "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="}
res = requests.post(f"{base_url}/session/{session_id}/frame", json=frame_data, headers=headers)
print("Frame Status:", res.json())

# 4. Finalize
fin = requests.post(f"{base_url}/session/{session_id}/finalize", json={"nonce": "2"}, headers=headers)
print("Result:", fin.json())
```

## Assumptions & Limitations
- **Model Choice**: Selected MediaPipe over depth/heavy CNN models to ensure high FPS on CPU and minimal dependencies. Very simple heuristics for Texture/Blur.
- **Deepfake/Masks**: Deepfake detection and silicone mask detection remain structural extension points. They require dedicated DL models (like ONNX models).
- **Depth Map**: True depth sensing is not assumed; geometry checks rely purely on monocular 2D landmarks layout.
- **Storage**: In-memory store handles local quick dev. Redis is meant for production token storage. PII raw images are actively dropped after processing.
