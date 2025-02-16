import logging
import uuid
from typing import Optional, Tuple

import aiohttp

from .repository import Repository
from .utils import create_response


class AuthService:
    def __init__(self, repository: Repository, logger=None):
        self.repository = repository
        self.logger = logger or logging.getLogger(__name__)

    async def authenticate(
        self, email: Optional[str] = None, user_token: Optional[str] = None
    ) -> Tuple[bool, str, dict]:
        """Handle user authentication"""
        if not self.repository.test_users:
            return (
                False,
                "",
                create_response(
                    flag="error", code=500, info="No test users configured"
                ),
            )

        test_user = None
        if email:
            test_user = next(
                (
                    user
                    for user in self.repository.test_users
                    if user["email"].lower() == email.lower()
                ),
                None,
            )
        elif user_token:
            test_user = next(
                (
                    user
                    for user in self.repository.test_users
                    if user["user_token"] == user_token
                ),
                None,
            )

        if not test_user:
            return (
                False,
                "",
                create_response(
                    flag="error",
                    code=410,
                    info="Authentication failed - No matching user found",
                ),
            )

        # Check for existing connection
        existing_connection = next(
            (
                (token, data)
                for token, data in self.repository.list_connections()
                if data["user"]["identity"]["emails"][0]["value"].lower()
                == test_user["email"].lower()
            ),
            None,
        )

        if existing_connection:
            connection_token = existing_connection[0]
        else:
            connection_token = str(uuid.uuid4())
            self.repository.store_connection_data(connection_token, test_user)

        return True, connection_token, create_response()

    async def process_callback(
        self, callback_uri: str, connection_token: str
    ) -> Tuple[bool, Optional[str], dict]:
        """Process callback request"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    callback_uri,
                    data={"connection_token": connection_token},
                    timeout=10,
                ) as callback_response:
                    if callback_response.status != 200:
                        response_text = await callback_response.text()
                        self.logger.error(
                            f"Callback request failed: {callback_response.status} {response_text}"
                        )
                        return (
                            False,
                            None,
                            create_response(
                                flag="error", code=500, info="Callback request failed"
                            ),
                        )

                    try:
                        redirect_url = (await callback_response.text()).strip('"')
                        return True, redirect_url, create_response()
                    except Exception as e:
                        self.logger.error(f"Failed to parse callback response: {e}")
                        return (
                            False,
                            None,
                            create_response(
                                flag="error",
                                code=500,
                                info="Invalid callback response format",
                            ),
                        )

        except aiohttp.ClientError as e:
            self.logger.error(f"Failed to make callback request: {e}")
            return (
                False,
                None,
                create_response(
                    flag="error", code=500, info="Failed to reach callback URL"
                ),
            )
