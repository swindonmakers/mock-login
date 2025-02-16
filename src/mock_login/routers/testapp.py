from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
import logging


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/testapp", tags=["testapp"])


@router.post("/callback", response_model=None)
async def handle_testapp_callback(request: Request):
    """Handle callback requests for Mock Login Test App"""
    data = await request.form()
    connection_token = data.get("connection_token")
    logger.info(f"Received callback request with connection token: {connection_token}")
    if not connection_token:
        logger.error("No connection token in callback request")
        return JSONResponse(
            status_code=200,
            content={
                "response": {
                    "request": {"status": {"flag": "success", "code": 200}},
                    "result": {
                        "status": {
                            "flag": "error",
                            "code": 400,
                            "info": "No connection token provided",
                        }
                    },
                }
            },
        )

    return "testapp/profile"


@router.get("/profile")
async def serve_testapp_profile():
    """Serve user profile page for Mock Login Test App"""
    try:
        with open("static/profile.html", "r") as f:
            content = f.read()
        return Response(content=content, media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail="Profile page (profile.html) not found"
        )

