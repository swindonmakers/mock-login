from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
import logging
from datetime import datetime

from ..dependencies import get_auth_service, get_repository
from ..models import AuthRequest, AuthResponse, UsersListResponse
from ..service import AuthService
from ..repository import Repository
from ..utils import create_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mock_oneall"])

@router.post("/socialize/login", response_model=AuthResponse)
async def mock_auth(request: AuthRequest, auth_service: Annotated[AuthService, Depends(get_auth_service)]):
    """
    Handle authentication requests.
    This endpoint authenticates users with social networks.
    Replaces what Google or GitHub does in the real service.
    """
    auth_data = request.data or {}
    success, connection_token, response = await auth_service.authenticate(
        email=auth_data.get('email'),
        user_token=auth_data.get('user_token')
    )
    
    if not success:
        return JSONResponse(status_code=200, content={"response": response})

    success, redirect_url, callback_response = await auth_service.process_callback(
        request.callback_uri,
        connection_token
    )

    if not success:
        return JSONResponse(status_code=200, content={"response": callback_response})

    return AuthResponse(
        connection_token=connection_token,
        redirect_url=redirect_url,
        response={
            **callback_response,
            "connection_token": connection_token,
            "redirect_url": redirect_url
        }
    )

@router.get("/users.json", response_model=UsersListResponse)
async def list_users(repository: Annotated[Repository, Depends(get_repository)]):
    """
    List all available users.
    A user is the data representation of a person that is using the OneAll plugins and services added to a website.
    See https://docs.oneall.com/api/resources/users/list-all-users/
    """
    return UsersListResponse(
        response=create_response(
            data={"users":{"entities": list(repository.test_users)}}
        )
    )

@router.get("/connections/{connection_token}.json", response_model=None)
async def get_connection(connection_token: str, repository: Annotated[Repository, Depends(get_repository)]):
    """
    Read connection details.
    The Connection API is used to retrieve the user's profile data after a login with a social network account.
    See https://docs.oneall.com/api/resources/connections/read-connection-details/
    """
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

@router.get("/connections.json", response_model=None)
async def list_connections(
    repository: Annotated[Repository, Depends(get_repository)],
    page: int = 1,
    entries_per_page: int = 50,
    order_by: str = "date_creation",
    order_dir: str = "asc",
):
    """
    List all connections with pagination.
    The Connection API is used to retrieve the user's profile data after a login with a social network account.
    See https://docs.oneall.com/api/resources/connections/list-all-connections/
    """
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

@router.get("/socialize/library.js")
async def serve_library():
    """
    Serve the Mock OneAll library.
    The library is used to authenticate users with social networks.
    This replaces the real OneAll library in the frontend.
    """
    try:
        with open("static/library.js", "r") as f:
            content = f.read()
        return Response(content=content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Library file (library.js) not found")
