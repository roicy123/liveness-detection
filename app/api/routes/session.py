from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api.schemas import SessionCreateResponse, ChallengeResponse
from app.core.session_manager import SessionManager
from app.core.security import create_session_token, verify_session_token
from app.services.active_challenge import generate_challenges
from datetime import datetime, timezone
from app.core.config import settings

router = APIRouter()

@router.post("", response_model=SessionCreateResponse)
def create_session():
    """
    Creates a new verification session.
    Returns session_id, token, and expiration timestamp.
    """
    session_id = SessionManager.create_session()
    token = create_session_token(session_id)
    expires_at = int((datetime.now(timezone.utc).timestamp() + settings.session_timeout_seconds))
    return SessionCreateResponse(session_id=session_id, token=token, expires_at=expires_at)

security = HTTPBearer()

@router.get("/{session_id}/challenge", response_model=ChallengeResponse)
def get_challenge(session_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Returns the randomized active-challenge sequence for this session.
    """
    token = credentials.credentials
    
    try:
        decoded = verify_session_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    if decoded.get("sub") != session_id:
        raise HTTPException(status_code=403, detail="Token sub does not match session ID")
        
    session_data = SessionManager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found or has expired")
        
    if not session_data.get("challenges"):
        # Generate new challenges if not present
        challenges = generate_challenges()
        session_data["challenges"] = challenges
        SessionManager.save_session(session_id, session_data)
        
    return ChallengeResponse(challenges=session_data["challenges"])
