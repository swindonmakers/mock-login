from pydantic import BaseModel, Field
from typing import Optional, Dict

class AuthRequest(BaseModel):
    callback_uri: str
    data: Optional[Dict[str, str]]

class AuthResponse(BaseModel):
    connection_token: str = Field(description="Connection token identifying the user session")
    redirect_url: Optional[str]
    response: dict

    model_config = {
        "json_schema_extra": {
            "example": [
                {
                    "connection_token": "123e4567-e89b-12d3-a456-426614174000",
                    "redirect_url": "https://example.com/callback",
                    "response": {
                        "request": {
                            "status": {"flag": "success", "code": 200}
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
            ]
        }
    }

class UserResponse(BaseModel):
    email: str
    user_token: str
    display_name: str

class UsersListResponse(BaseModel):
    response: dict
