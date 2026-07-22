import pytest
from app.services.active_challenge import check_smile, check_open_mouth, check_head_turn

@pytest.fixture
def mock_neutral_landmarks():
    # 468 points, initialize to 0
    lm = [(0.0, 0.0, 0.0)] * 468
    # Mouth corners 61, 291
    lm[61] = (0.4, 0.5, 0.0)
    lm[291] = (0.6, 0.5, 0.0)
    # Mouth top 0, bottom 17
    lm[0] = (0.5, 0.45, 0.0)
    lm[17] = (0.5, 0.55, 0.0)
    # Inner mouth 13, 14
    lm[13] = (0.5, 0.48, 0.0)
    lm[14] = (0.5, 0.52, 0.0)
    # Face top 10, chin 152
    lm[10] = (0.5, 0.1, 0.0)
    lm[152] = (0.5, 0.9, 0.0)
    # Nose 1, Eyes 33, 263
    lm[1] = (0.5, 0.5, 0.0)
    lm[33] = (0.3, 0.4, 0.0)
    lm[263] = (0.7, 0.4, 0.0)
    return lm

def test_smile_fail(mock_neutral_landmarks):
    # Neutral resting face W=0.2, H=0.1. Ratio = 2.0 (below 2.4 threshold)
    score = check_smile(mock_neutral_landmarks)
    assert score == 0.0
    
def test_smile_pass(mock_neutral_landmarks):
    # Stretch corners wide
    mock_neutral_landmarks[61] = (0.3, 0.5, 0.0)
    mock_neutral_landmarks[291] = (0.7, 0.5, 0.0)
    score = check_smile(mock_neutral_landmarks)
    assert score == 1.0 # W=0.4, H=0.1, Ratio=4.0 > 2.8

def test_open_mouth_fail(mock_neutral_landmarks):
    session_data = {}
    # First call sets baseline
    check_open_mouth(mock_neutral_landmarks, session_data)
    score = check_open_mouth(mock_neutral_landmarks, session_data)
    assert score == 0.0

def test_open_mouth_pass(mock_neutral_landmarks):
    session_data = {}
    check_open_mouth(mock_neutral_landmarks, session_data)
    
    # Open jaw heavily
    mock_neutral_landmarks[14] = (0.5, 0.65, 0.0)
    score = check_open_mouth(mock_neutral_landmarks, session_data)
    assert score == 1.0

def test_head_turn_right_pass(mock_neutral_landmarks):
    # Face turns right, nose shifts left relative to camera
    mock_neutral_landmarks[1] = (0.6, 0.5, 0.0)
    # dist to left eye = 0.3. dist to right eye = 0.1
    # Turn right ratio = 0.3 / 0.1 = 3.0 > 1.8
    score = check_head_turn(mock_neutral_landmarks, "turn_right")
    assert score == 1.0
