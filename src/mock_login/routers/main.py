from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter()


@router.get(
    "/",
    tags=["testapp"],
    responses={
        200: {
            "content": {"text/html": {}},
            "description": "Login page for Mock Login Test App",
        },
        404: {
            "content": {"text/html": {}},
            "description": "Login page not found",
        },
    },
)
async def serve_testapp_index() -> HTMLResponse:
    """Serve a basic HTML page for Mock Login Test App"""
    try:
        with open("static/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Index file (index.html) not found")


@router.get("/health", tags=["internal"])
async def health_check() -> JSONResponse:
    """Health check endpoint"""
    return JSONResponse(
        content={"status": "ok"},
    )
