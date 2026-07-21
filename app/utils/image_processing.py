import cv2
import numpy as np
import base64

def base64_to_image(base64_string: str) -> np.ndarray:
    """Decodes a base64 string to a cv2 BGR image."""
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    
    img_data = base64.b64decode(base64_string)
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Invalid image or failed to decode base64 payload")
    return img

def strip_exif(img: np.ndarray) -> np.ndarray:
    """cv2.imdecode automatically strips EXIF data, so this is mostly a conceptual pass-through or normalization step."""
    # The requirement asks to strip EXIF from any stored frame. 
    # Because OpenCV ignores EXIF when decoding to numpy, the raw data is already 'clean'.
    return img
