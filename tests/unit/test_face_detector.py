import pytest
import numpy as np
from app.services.face_detector import detect_face, FaceDetectionError

def test_no_face_detect():
    # Blank image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    with pytest.raises(FaceDetectionError) as excinfo:
        detect_face(img)
    assert excinfo.value.reason_code == "NO_FACE_DETECTED"
