from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api.schemas import VerifyFrameRequest, FrameStatusResponse, FinalizeRequest, FinalizeResponse
from app.core.session_manager import SessionManager
from app.core.security import verify_session_token
from app.utils.image_processing import base64_to_image, strip_exif
from app.services.face_detector import detect_face, FaceDetectionError
from app.services.passive_liveness import evaluate_passive_liveness
from app.services.spoof_detector import evaluate_spoofing
from app.services.decision_fusion import fuse_session_decisions

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
def submit_frame(session_id: str, req: VerifyFrameRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    session_data = _get_verified_session(session_id, credentials.credentials)
    
    if not SessionManager.validate_nonce(session_id, session_data, req.nonce):
        raise HTTPException(status_code=422, detail="Nonce has already been used")

    try:
        image = base64_to_image(req.image_base64)
        image = strip_exif(image)
        
        face_data = detect_face(image)
        passive_scores = evaluate_passive_liveness(image, face_data)
        spoof_scores = evaluate_spoofing(passive_scores, session_data)
        
        accumulated = session_data["accumulated_data"]
        accumulated["frames_analyzed"] = accumulated.get("frames_analyzed", 0) + 1
        
        if "passive_scores" not in accumulated:
            accumulated["passive_scores"] = []
        accumulated["passive_scores"].append(passive_scores)
        
        if "spoof_scores" not in accumulated:
            accumulated["spoof_scores"] = []
        accumulated["spoof_scores"].append(spoof_scores)
        
        # Simplified active challenge tracking
        req_ch = session_data.get("challenges", [])
        ch_idx = session_data.get("challenge_index", 0)
        
        if ch_idx < len(req_ch):
            # Assumes challenge is passed for this frame
            accumulated["active_pass_count"] = accumulated.get("active_pass_count", 0) + 1
            session_data["challenge_index"] = ch_idx + 1
            status = "in_progress"
        else:
            status = "ready_to_finalize"

        SessionManager.save_session(session_id, session_data)
        return FrameStatusResponse(status=status)
        
    except FaceDetectionError as e:
        return FrameStatusResponse(status="rejected", rejected_reason=e.reason_code)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Image processing error: {str(e)}")
    except Exception as e:
        # Graceful degradation on error
        return FrameStatusResponse(status="rejected", rejected_reason=f"Processing error: {str(e)}")

@router.post("/{session_id}/finalize", response_model=FinalizeResponse)
def finalize_session(session_id: str, req: FinalizeRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    session_data = _get_verified_session(session_id, credentials.credentials)
    
    if not SessionManager.validate_nonce(session_id, session_data, req.nonce):
        raise HTTPException(status_code=422, detail="Nonce has already been used")

    fusion_result = fuse_session_decisions(session_data)
    
    return FinalizeResponse(
        classification=fusion_result["classification"], 
        confidence=fusion_result["confidence"],
        reasons=fusion_result["reasons"]
    )
