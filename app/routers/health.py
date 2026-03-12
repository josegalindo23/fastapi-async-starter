"""
app/routers/health.py

Health check endpoint:
    GET /health - Simple endpoint to verify API is running
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "message": "API is running smoothly."}