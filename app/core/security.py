import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings

def create_session_token(session_id: str) -> str:
    """Create a JWT token matching a specific session ID"""
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.session_timeout_seconds)
    payload = {
        "sub": session_id,
        "exp": expires_at,
        "iat": datetime.now(timezone.utc)
    }
    encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_session_token(token: str) -> dict:
    """Verify standard JWT standard claims"""
    try:
        decoded_token = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
