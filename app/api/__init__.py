from fastapi import APIRouter
from app.api.routes import session, verify, health

api_router = APIRouter()
api_router.include_router(session.router, prefix="/session", tags=["Session"])
api_router.include_router(verify.router, prefix="/session", tags=["Verify"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
