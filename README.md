# Liveness Detection API

A production-grade, REST-API-driven facial liveness detection system built in Python. This system classifies verification sessions as **Live Person**, **Spoof Attack**, or **Unable to Verify** by combining passive CV checks, active randomized challenge-response gating, and spoof detection thresholds via a Decision Fusion Engine.

## Core Features

* **Passive Liveness Checks:** Uses classical CV logic (Laplacian variance, 2D FFT, specular reflection mapping) to detect static printed photos and screen glares. Also implements depth variance cues and ambient lighting jump-detection.
* **Active Challenge Gating:** Enforces real-time geometric facial mapping. Randomly issues 3 tasks with a 10-second timeout limit each:
  * `blink`: Computes Eye Aspect Ratios (EAR) across historical frames to detect natural micro-blinks.
  * `smile`: Maps Mouth Aspect Ratios (MAR) to catch horizontal corner stretching.
  * `open_mouth`: Normalizes vertical lip distances.
  * `turn_left` & `turn_right`: Mirror-agnostic spatial tracking for horizontal head movement.
  * `look_up` & `look_down`: Tracks pitch alignment via nose-to-eye vertical offsets.
  * `raise_eyebrows`: Detects relative vertical jumps in inner eyebrows.
* **Decision Fusion Engine:** Mathematically weights exact active task successes, tracks passive frame anomalies, and subtracts spoof penalties to compute an end-to-end Confidence float.
* **Rate Limiting & Security:** Integrated JWT authorization state handling and heavily rate-limited session routes via `slowapi` to protect against bots.
* **Audit Logging:** Structured, PII-safe JSON logging tracking `Session Created`, `Timeouts`, and `Classifications` via `python-json-logger`.
* **Zero-Dependency Frontend:** Includes a completely bare-bones HTML/Vanilla JS client to live-debug the API asynchronously directly from your browser.

## Tech Stack

* **Backend:** FastAPI, Python 3.11+
* **Computer Vision:** OpenCV, MediaPipe Face Mesh
* **State & Performance:** Redis (with local In-Memory Fallback), PyJWT
* **Testing Suite:** Pytest (Unit, Geometric, & Integration flow testing)

## Getting Started

### 1. Run using Docker (Recommended)
Automatically builds the backend environment alongside a local Redis state container.
```bash
docker-compose up --build
```

### 2. Run locally via Python Virtual Environment
```bash
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## How to Test the Demo Frontend
The system ships with a fully automated, client-side browser playground for live review processes. 

Once the API server is running, simply open your favorite browser and visit:
👉 **[http://localhost:8000/demo/index.html](http://localhost:8000/demo/index.html)**

Click *Start Session*, allow Camera access, and perform the 3 randomly generated challenges! The browser will autonomously stream frames to the backend via polling, instantly transition on passing thresholds or timeouts, and mathematically classify your physical liveness.

### How to physically perform the challenges:
* **`turn_left`**: Turn your actual physical head to the **left** side of your desk. (Do *not* try to match the mirror image on your screen—just turn your real left!).
* **`turn_right`**: Turn your actual physical head to the **right**.
* **`look_up`**: Tilt your chin up towards the ceiling.
* **`look_down`**: Tuck your chin slightly down towards your chest.
* **`smile`**: Flare the corners of your mouth out horizontally to bare your teeth. (A wide grin works best).
* **`open_mouth`**: Drop your jaw visibly. An exaggerated "AHHH" sound gives the best vertical clearance.
* **`raise_eyebrows`**: Lift your eyebrows up away from your eyes like you are extremely surprised!
* **`blink`**: Close both eyes fully for a distinct second, then open them wide. Make it a deliberate blink rather than a rapid micro-twitch!

## Architecture & API Route Lifecycle

The platform is designed for scalable microservice environments:
1. `POST /session` -> Initializes a localized session JWT token and binds the active random challenges arrays. Rate-limited to 5/min per IP.
2. `GET /session/{id}/challenge` -> Issues the active checklist instructions.
3. `POST /session/{id}/frame` -> Ingests Base64 frames (capped at 20 frames/sec), routing them heavily through MediaPipe face validation, active threshold loops, and spoof variance models. 
4. `POST /session/{id}/finalize` -> The Fusion array collapses the frame histories and outputs a clean `live_person`, `spoof_attack`, or `unable_to_verify` JSON response payload.
