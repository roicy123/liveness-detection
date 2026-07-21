# Liveness Detection API

A REST-API based facial liveness verification suite designed to classify presentation attacks vs live actors. Computes continuous geometric baselines, depth cues, and passive tracking thresholds to produce a confidence score via late decision fusion.

## Architecture

```text
liveness-detection/
├── app/
│   ├── api/routes/      # FastAPI endpoint definitions
│   ├── core/            # Rate limiting, security, Redis sessions, and config
│   ├── services/        # CV pipelines (Mediapipe face mesh, active challenges, spoofing)
│   └── utils/           # Structured JSON auditing and image/exif parsing
├── tests/               # Pytest suite (integration & unit)
├── frontend/            # Vanilla JS diagnostic demo interface
└── docker-compose.yml
```

## Setup & Execution

### Docker (Recommended)
Boot the backend environments with the Redis dependency attached:
```bash
docker-compose up --build
```

### Local Virtual Environment
```bash
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API Docs: `http://localhost:8000/docs`
Diagnostic Demo UI: `http://localhost:8000/demo/index.html`

## Testing

Execute the test suite using pytest to measure edge cases and integration validation bounds.
```bash
python run_tests.py
# Or directly:
pytest tests/ -v
```
