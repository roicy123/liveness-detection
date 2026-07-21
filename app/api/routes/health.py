from fastapi import APIRouter

router = APIRouter()

@router.get("")
def health_check():
    """
    Liveness/readiness probe for the service itself.
    Returns HTTP 200 if the service is up.
    """
    return {"status": "ok"}
