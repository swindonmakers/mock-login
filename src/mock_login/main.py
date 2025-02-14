from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import aiohttp
from contextlib import asynccontextmanager
from pathlib import Path
import os
import logging
from typing import Optional, Dict, List
from datetime import datetime

from mock_login.repository import Repository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the application state"""
    global repository
    repository = Repository()
    yield

app = FastAPI(title="Mock OneAll Service", lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/socialize", StaticFiles(directory="static"), name="socialize")

# Model definitions
class AuthRequest(BaseModel):
    callback_uri: str
    data: Optional[Dict[str, str]]

class AuthResponse(BaseModel):
    connection_token: str
    redirect_url: Optional[str]
    response: dict

    class Config:
        json_schema_extra = {
            "example": {
                "connection_token": "123e4567-e89b-12d3-a456-426614174000",
                "redirect_url": "https://example.com/callback",
                "response": {
                    "request": {
                        "status": {
                            "flag": "success",
                            "code": 200
                        }
                    },
                    "result": {
                        "status": {
                            "flag": "error",
                            "code": 500,
                            "info": "Invalid callback response format"
                        }
                    }
                }
            }
        }

# Global state
connections: Dict[str, dict] = {}
test_users = []

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/mock-oneall/auth", response_model=AuthResponse)
async def mock_auth(request: AuthRequest):
    """Handle authentication requests"""
    if not repository.test_users:
        raise HTTPException(status_code=500, detail="No test users configured")

    # Find matching test user
    test_user = None
    if request.data:
        if 'email' in request.data:
            test_user = next(
                (user for user in repository.test_users if user['email'].lower() == request.data['email'].lower()),
                None
            )
        elif 'user_token' in request.data:
            test_user = next(
                (user for user in repository.test_users if user['user_token'] == request.data['user_token']),
                None
            )

    if not test_user:
        logger.warning("No matching test user found")
        return JSONResponse(
            status_code=200,  # OneAll returns 200 even for auth failures
            content={
                "response": {
                    "request": {
                        "date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z"),
                        "status": {
                            "flag": "success",
                            "code": 200
                        }
                    },
                    "result": {
                        "status": {
                            "flag": "error",
                            "code": 410,
                            "info": "Authentication failed - No matching user found"
                        }
                    }
                }
            }
        )
    
    # Check for existing connection with same email
    existing_connection = next(
        (
            (token, data) for token, data in repository.list_connections()
            if data["user"]["identity"]["emails"][0]["value"].lower() == test_user["email"].lower()
        ),
        None
    )

    if existing_connection:
        connection_token = existing_connection[0]
    else:
        # Generate a new connection token
        connection_token = str(uuid.uuid4())
        repository.store_connection_data(connection_token, test_user)
    
    redirect_url = None

    # Make callback POST request
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                request.callback_uri,
                data={"connection_token": connection_token},
                timeout=10
            ) as callback_response:
                logger.info(f"Callback request to {request.callback_uri} returned {callback_response.status}")
                logger.info(f"Callback headers: {callback_response.headers}")
                
                if callback_response.status != 200:
                    response_text = await callback_response.text()
                    logger.error(f"Callback request failed: {callback_response.status} {response_text}")
                    return JSONResponse(
                        status_code=200,
                        content={
                            "response": {
                                "request": {
                                    "status": {
                                        "flag": "success",
                                        "code": 200
                                    }
                                },
                                "result": {
                                    "status": {
                                        "flag": "error",
                                        "code": 500,
                                        "info": "Callback request failed"
                                    }
                                }
                            }
                        }
                    )
                
                # Get redirect URL from response
                try:
                    redirect_url = (await callback_response.text()).strip('"')
                    logger.info(f"Got redirect URL from callback: {redirect_url}")
                except Exception as e:
                    logger.error(f"Failed to parse callback response: {e}")
                    return JSONResponse(
                        status_code=200,
                        content={
                            "response": {
                                "request": {
                                    "status": {
                                        "flag": "success",
                                        "code": 200
                                    }
                                },
                                "result": {
                                    "status": {
                                        "flag": "error",
                                        "code": 500,
                                        "info": "Invalid callback response format"
                                    }
                                }
                            }
                        }
                    )
                
    except aiohttp.ClientError as e:
        logger.error(f"Failed to make callback request: {e}")
        return JSONResponse(
            status_code=200,
            content={
                "response": {
                    "request": {
                        "status": {
                            "flag": "success",
                            "code": 200
                        }
                    },
                    "result": {
                        "status": {
                            "flag": "error",
                            "code": 500,
                            "info": "Failed to reach callback URL"
                        }
                    }
                }
            }
        )

    return AuthResponse(
        connection_token=connection_token,
        redirect_url=redirect_url,
        response={
            "request": {
                "status": {
                    "flag": "success",
                    "code": 200
                }
            },
            "result": {
                "status": {
                    "flag": "success",
                    "code": 200,
                        "info": "The user successfully authenticated"
                }
            },
            "connection_token": connection_token,
            "redirect_url": redirect_url
            },
        )


@app.get("/mock-oneall/users")
async def list_test_users():
    """List available test users"""
    return {
        "response": {
            "request": {
                "status": {
                    "flag": "success",
                    "code": 200
                }
            },
            "result": {
                "data": {
                    "users": [
                        {
                            "email": user["email"],
                            "user_token": user["user_token"],
                            "display_name": user["display_name"]
                        }
                        for user in repository.test_users
                    ]
                }
            }
        }
    }

@app.get("/connections/{connection_token}.json")
async def get_connection(connection_token: str):
    """Retrieve connection details"""
    connection = repository.get_connection(connection_token)
    if not connection:
        return JSONResponse(
            status_code=404,
            content={
                "response": {
                    "request": {
                        "date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z"),
                        "resource": f"/connections/{connection_token}.json",
                        "status": {
                            "flag": "error",
                            "code": 404,
                            "info": "Connection not found"
                        }
                    }
                }
            }
        )

    return {
        "response": {
            "request": {
                "resource": f"/connections/{connection_token}.json",
                "status": {
                    "flag": "success",
                    "code": 200
                }
            },
            "result": {
                "status": {
                    "flag": "success",
                    "code": 200,
                    "info": "The user successfully authenticated"
                },
                "data": connection
            }
        }
    }

@app.get("/connections.json")
async def list_connections(
    page: int = 1,
    entries_per_page: int = 50,
    order_by: str = "date_creation",
    order_dir: str = "asc"
):
    """List all connections with pagination"""
    # Get all connections as list and sort them
    all_connections = repository.list_connections()
    
    # Sort connections
    if order_by == "date_creation":
        all_connections.sort(
            key=lambda x: x[1]["connection"]["date"],
            reverse=(order_dir.lower() == "desc")
        )
    
    # Calculate pagination
    total_entries = len(all_connections)
    total_pages = (total_entries + entries_per_page - 1) // entries_per_page
    start_idx = (page - 1) * entries_per_page
    end_idx = min(start_idx + entries_per_page, total_entries)
    
    # Get paginated connections
    paginated_connections = all_connections[start_idx:end_idx]
    
    # Format response according to OneAll API specification
    return {
        "response": {
            "request": {
                "date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z"),
                "resource": "/connections.json",
                "status": {
                    "flag": "success",
                    "code": 200,
                    "info": "Your request has been processed successfully"
                }
            },
            "result": {
                "data": {
                    "connections": {
                        "pagination": {
                            "current_page": page,
                            "total_pages": total_pages,
                            "entries_per_page": entries_per_page,
                            "total_entries": total_entries,
                            "order": {
                                "field": order_by,
                                "direction": order_dir
                            }
                        },
                        "count": len(paginated_connections),
                        "entries": [
                            {
                                "connection_token": token,
                                "email": data["user"]["identity"]["emails"][0]["value"],
                                "status": "succeeded",
                                "date_creation": data["connection"]["date"]
                            }
                            for token, data in paginated_connections
                        ]
                    }
                }
            }
        }
    }

@app.get("/socialize/library.js")
async def serve_library():
    """Serve the mock OneAll library"""
    try:
        with open("static/library.js", "r") as f:
            content = f.read()
        return Response(content=content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Library file (library.js) not found")


@app.get("/")
async def serve_testapp_index():
    """Serve a basic HTML page"""
    try:
        with open("static/index.html", "r") as f:
            content = f.read()
        return Response(content=content, media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Index file (index.html) not found")

@app.post("/testapp/callback")
async def handle_testapp_callback(request: Request):
    """Handle callback requests"""
    data = await request.form()
    connection_token = data.get("connection_token")
    logger.info(f"Received callback request with connection token: {connection_token}")
    if not connection_token:
        logger.error("No connection token in callback request")
        return JSONResponse(
            status_code=200,
            content={
                "response": {
                    "request": {
                        "status": {
                            "flag": "success",
                            "code": 200
                        }
                    },
                    "result": {
                        "status": {
                            "flag": "error",
                            "code": 400,
                            "info": "No connection token provided"
                        }
                    }
                }
            }
        )

    return "testapp/profile"

@app.get("/testapp/profile")
async def serve_testapp_profile():
    """Serve user profile page"""
    try:
        with open("static/profile.html", "r") as f:
            content = f.read()
        return Response(content=content, media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Profile page (profile.html) not found")
