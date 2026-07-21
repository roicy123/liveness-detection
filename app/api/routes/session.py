from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api.schemas import SessionCreateResponse, ChallengeResponse
from app.core.session_manager import SessionManager
from app.core.security import create_session_token, verify_session_token
from app.services.active_challenge import generate_challenges
from datetime import datetime, timezone
from app.core.config import settings
from app.core.rate_limit import limiter
from app.utils.logging import audit_logger

router = APIRouter()
security = HTTPBearer()

@router.post("", response_model=SessionCreateResponse)
@limiter.limit("5/minute")
def create_session(request: Request):
    """
    Creates a new verification session.
    """
    session_id = SessionManager.create_session()
    token = create_session_token(session_id)
    expires_at = int((datetime.now(timezone.utc).timestamp() + settings.session_timeout_seconds))
    
    audit_logger.info("Session created", extra={"session_id": session_id})
    return SessionCreateResponse(session_id=session_id, token=token, expires_at=expires_at)

@router.get("/{session_id}/challenge", response_model=ChallengeResponse)
def get_challenge(session_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded = verify_session_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    if decoded.get("sub") != session_id:
        raise HTTPException(status_code=403, detail="Token sub mismatch")
        
    session_data = SessionManager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session expired or not found")
        
    if not session_data.get("challenges"):
        challenges = generate_challenges()
        session_data["challenges"] = challenges
        session_data["challenge_start_time"] = datetime.now(timezone.utc).timestamp()
        SessionManager.save_session(session_id, session_data)
        audit_logger.info("Challenge issued", extra={"session_id": session_id, "challenges": challenges})
        
    return ChallengeResponse(challenges=session_data["challenges"])
