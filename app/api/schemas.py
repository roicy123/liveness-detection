from pydantic import BaseModel, Field
from typing import List, Optional

# Requests
class VerifyFrameRequest(BaseModel):
    nonce: str = Field(..., description="Unique nonce for the request to prevent replay")
    image_base64: str = Field(..., description="Base64 encoded image frame")
    
class FinalizeRequest(BaseModel):
    nonce: str = Field(..., description="Unique nonce for the request to prevent replay")

# Responses
class SessionCreateResponse(BaseModel):
    session_id: str
    token: str
    expires_at: int

class ChallengeResponse(BaseModel):
    challenges: List[str]

class FrameStatusResponse(BaseModel):
    status: str = Field(..., description="'in_progress', 'rejected', or 'ready_to_finalize'")
    rejected_reason: Optional[str] = None
    
class FinalizeResponse(BaseModel):
    classification: str = Field(..., description="'live_person', 'spoof_attack', or 'unable_to_verify'")
    confidence: float
    reasons: List[str]
