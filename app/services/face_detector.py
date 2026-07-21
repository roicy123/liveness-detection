import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, Any

mp_face_mesh = mp.solutions.face_mesh

# Initialize single instance per worker
face_mesh_detector = mp_face_mesh.FaceMesh(
    static_image_mode=True, 
    max_num_faces=3, 
    refine_landmarks=True, 
    min_detection_confidence=0.5
)

class FaceDetectionError(Exception):
    def __init__(self, reason_code: str, message: str):
        self.reason_code = reason_code
        self.message = message
        super().__init__(self.message)

def detect_face(image: np.ndarray) -> Dict[str, Any]:
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh_detector.process(rgb_image)
    
    if not results.multi_face_landmarks:
        raise FaceDetectionError("NO_FACE_DETECTED", "No face was detected in the frame")
        
    if len(results.multi_face_landmarks) > 1:
        raise FaceDetectionError("MULTIPLE_FACES_DETECTED", "More than one face detected")
        
    landmarks = results.multi_face_landmarks[0]
    
    h, w, _ = image.shape
    x_min, y_min = w, h
    x_max, y_max = 0, 0
    
    landmark_list = []
    
    for lm in landmarks.landmark:
        x, y = int(lm.x * w), int(lm.y * h)
        landmark_list.append((x, y, lm.z))
        if x < x_min: x_min = x
        if y < y_min: y_min = y
        if x > x_max: x_max = x
        if y > y_max: y_max = y
        
    bbox_w = x_max - x_min
    bbox_h = y_max - y_min
    
    # Reject if face bounding box is too small relative to frame
    if bbox_w < (w * 0.15) or bbox_h < (h * 0.15):
        raise FaceDetectionError("FACE_TOO_SMALL", "Face is too far from the camera")
        
    # Checking boundaries for heavy occlusion / cropping
    if x_min < 0 or y_min < 0 or x_max > w or y_max > h:
        raise FaceDetectionError("FACE_PARTIAL_OR_OCCLUDED", "Face landmarks fall outside frame bounds")
        
    return {
        "bbox": (x_min, y_min, bbox_w, bbox_h),
        "landmarks": landmark_list,
        "normalized_landmarks": landmarks
    }
