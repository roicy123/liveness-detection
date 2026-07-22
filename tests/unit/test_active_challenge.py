import pytest
from app.services.active_challenge import check_smile, check_open_mouth, check_head_turn

@pytest.fixture
def mock_neutral_landmarks():
    lm = [(0.0, 0.0, 0.0)] * 468
    lm[61] = (0.4, 0.5, 0.0)
    lm[291] = (0.6, 0.5, 0.0)
    lm[0] = (0.5, 0.45, 0.0)
    lm[17] = (0.5, 0.55, 0.0)
    lm[13] = (0.5, 0.48, 0.0)
    lm[14] = (0.5, 0.52, 0.0)
    lm[10] = (0.5, 0.1, 0.0)
    lm[152] = (0.5, 0.9, 0.0)
    lm[1] = (0.5, 0.5, 0.0)
    lm[33] = (0.3, 0.4, 0.0)
    lm[263] = (0.7, 0.4, 0.0)
    lm[234] = (0.3, 0.5, 0.0)
    lm[454] = (0.7, 0.5, 0.0)
    return lm

def test_smile_fail(mock_neutral_landmarks):
    session_data = {}
    check_smile(mock_neutral_landmarks, session_data)
    score = check_smile(mock_neutral_landmarks, session_data)
    assert score == 0.0

def test_smile_pass(mock_neutral_landmarks):
    session_data = {}
    check_smile(mock_neutral_landmarks, session_data)
    mock_neutral_landmarks[61] = (0.3, 0.5, 0.0)
    mock_neutral_landmarks[291] = (0.7, 0.5, 0.0)
    score = check_smile(mock_neutral_landmarks, session_data)
    assert score == 1.0

def test_open_mouth_fail(mock_neutral_landmarks):
    session_data = {}
    check_open_mouth(mock_neutral_landmarks, session_data)
    score = check_open_mouth(mock_neutral_landmarks, session_data)
    assert score == 0.0

def test_open_mouth_pass(mock_neutral_landmarks):
    session_data = {}
    check_open_mouth(mock_neutral_landmarks, session_data)
    mock_neutral_landmarks[14] = (0.5, 0.65, 0.0)
    score = check_open_mouth(mock_neutral_landmarks, session_data)
    assert score == 1.0

def test_head_turn_right_pass(mock_neutral_landmarks):
    session_data = {}
    check_head_turn(mock_neutral_landmarks, "turn_right", session_data)
    mock_neutral_landmarks[1] = (0.6, 0.5, 0.0)
    score = check_head_turn(mock_neutral_landmarks, "turn_right", session_data)
    assert score == 1.0
