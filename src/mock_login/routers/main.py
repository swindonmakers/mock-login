from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", tags=["testapp"])
async def serve_testapp_index():
    """Serve a basic HTML page for Mock Login Test App"""
    try:
        with open("static/index.html", "r") as f:
            content = f.read()
        return Response(content=content, media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Index file (index.html) not found")


@router.get("/health", tags=["internal"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
