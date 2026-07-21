import pytest
import numpy as np
from app.services.passive_liveness import check_blur, check_texture

def test_check_blur_sharp():
    # Random noise looks like high frequency sharp details to Laplacian
    img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    score = check_blur(img)
    assert score > 0.8

def test_check_blur_blurry():
    img = np.ones((200, 200, 3), dtype=np.uint8) * 128
    score = check_blur(img)
    assert score < 0.2
