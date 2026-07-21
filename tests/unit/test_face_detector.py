import pytest
import numpy as np
from app.services.face_detector import detect_face, FaceDetectionError

def test_no_face_detect():
    # Blank image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    with pytest.raises(FaceDetectionError) as excinfo:
        detect_face(img)
    assert excinfo.value.reason_code == "NO_FACE_DETECTED"

def test_multi_face_reject(monkeypatch):
    import app.services.face_detector
    
    class MockFaceMesh:
        def process(self, image):
            class MockResults:
                multi_face_landmarks = [1, 2] # Simulating 2 faces
            return MockResults()
            
    monkeypatch.setattr(app.services.face_detector, "face_mesh_detector", MockFaceMesh())
    
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    with pytest.raises(FaceDetectionError) as excinfo:
        detect_face(img)
    assert excinfo.value.reason_code == "MULTIPLE_FACES_DETECTED"
