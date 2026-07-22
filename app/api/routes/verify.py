from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api.schemas import VerifyFrameRequest, FrameStatusResponse, FinalizeRequest, FinalizeResponse
from app.core.session_manager import SessionManager
from app.core.security import verify_session_token
from app.utils.image_processing import base64_to_image, strip_exif
from app.services.face_detector import detect_face, FaceDetectionError
from app.services.passive_liveness import evaluate_passive_liveness
from app.services.spoof_detector import evaluate_spoofing
from app.services.decision_fusion import fuse_session_decisions
from app.services.active_challenge import (
    check_blink, check_smile, check_open_mouth, 
    check_head_turn, check_raise_eyebrows
)
import time
from app.core.rate_limit import limiter
from app.utils.logging import audit_logger

router = APIRouter()
security = HTTPBearer()

def _get_verified_session(session_id: str, token: str):
    try:
        decoded = verify_session_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    if decoded.get("sub") != session_id:
        raise HTTPException(status_code=403, detail="Token sub mismatch")
        
    session_data = SessionManager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session expired or not found")
        
    return session_data

@router.post("/{session_id}/frame", response_model=FrameStatusResponse)
@limiter.limit("20/second")
def submit_frame(request: Request, session_id: str, req: VerifyFrameRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    session_data = _get_verified_session(session_id, credentials.credentials)
    
    if not SessionManager.validate_nonce(session_id, session_data, req.nonce):
        raise HTTPException(status_code=422, detail="Nonce has already been used")

    try:
        image = base64_to_image(req.image_base64)
        image = strip_exif(image)
        
        face_data = detect_face(image)
        landmarks = face_data["landmarks"]
        
        passive_scores = evaluate_passive_liveness(image, face_data, session_data)
        spoof_scores = evaluate_spoofing(passive_scores, session_data)
        
        accumulated = session_data["accumulated_data"]
        accumulated["frames_analyzed"] = accumulated.get("frames_analyzed", 0) + 1
        
        if "passive_scores" not in accumulated:
            accumulated["passive_scores"] = []
        accumulated["passive_scores"].append(passive_scores)
        
        if "spoof_scores" not in accumulated:
            accumulated["spoof_scores"] = []
        accumulated["spoof_scores"].append(spoof_scores)
        
        req_ch = session_data.get("challenges", [])
        ch_idx = session_data.get("challenge_index", 0)
        
        if ch_idx < len(req_ch):
            current_challenge = req_ch[ch_idx]
            ch_start_time = session_data.get("challenge_start_time", 0)
            elapsed = time.time() - ch_start_time
            
            # Response window logic (10s max per challenge)
            max_wait = 10.0
            
            if elapsed > max_wait:
                audit_logger.info("Frame rejected", extra={"session_id": session_id, "reason": "Challenge timeout expired"})
                
                failed_chals = session_data.setdefault("failed_challenges", [])
                failed_chals.append(current_challenge)
                
                session_data["challenge_index"] = ch_idx + 1 # Fail and advance
                session_data["challenge_start_time"] = time.time()
                SessionManager.save_session(session_id, session_data)
                return FrameStatusResponse(status="rejected", rejected_reason="Challenge timed out")

            if current_challenge == "blink":
                score = check_blink(landmarks, session_data)
            elif current_challenge == "smile":
                score = check_smile(landmarks, session_data)
            elif current_challenge == "open_mouth":
                score = check_open_mouth(landmarks, session_data)
            elif current_challenge in ["turn_left", "turn_right", "look_up", "look_down"]:
                score = check_head_turn(landmarks, current_challenge, session_data)
            elif current_challenge == "raise_eyebrows":
                score = check_raise_eyebrows(landmarks, session_data)
                
            if score >= 0.45:
                accumulated["active_pass_count"] = accumulated.get("active_pass_count", 0) + 1
                session_data["challenge_index"] = ch_idx + 1
                session_data["challenge_start_time"] = time.time() 
                
            status = "in_progress"
        else:
            status = "ready_to_finalize"

        SessionManager.save_session(session_id, session_data)
        return FrameStatusResponse(status=status)
        
    except FaceDetectionError as e:
        audit_logger.info("Frame rejected", extra={"session_id": session_id, "reason": e.reason_code})
        return FrameStatusResponse(status="rejected", rejected_reason=e.reason_code)
    except ValueError as e:
        audit_logger.error("Image error", extra={"session_id": session_id, "error": str(e)})
        raise HTTPException(status_code=422, detail=f"Image processing error: {str(e)}")
    except Exception as e:
        audit_logger.error("System error", extra={"session_id": session_id, "error": str(e)})
        return FrameStatusResponse(status="rejected", rejected_reason=f"Processing error: {str(e)}")

@router.post("/{session_id}/finalize", response_model=FinalizeResponse)
def finalize_session(session_id: str, req: FinalizeRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    session_data = _get_verified_session(session_id, credentials.credentials)
    
    if not SessionManager.validate_nonce(session_id, session_data, req.nonce):
        raise HTTPException(status_code=422, detail="Nonce has already been used")
        
    SessionManager.save_session(session_id, session_data)

    try:
        fusion_result = fuse_session_decisions(session_data)
    except Exception as e:
        audit_logger.error("Fusion error", extra={"session_id": session_id, "error": str(e)})
        fusion_result = {
            "classification": "unable_to_verify", 
            "confidence": 0.0,
            "reasons": [f"Decision fusion pipeline failed: {str(e)}"]
        }
    
    audit_logger.info("Session finalized", extra={
        "session_id": session_id, 
        "classification": fusion_result["classification"],
        "confidence": fusion_result["confidence"]
    })
    
    return FinalizeResponse(
        classification=fusion_result["classification"], 
        confidence=fusion_result["confidence"],
        reasons=fusion_result["reasons"]
    )
