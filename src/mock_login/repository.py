import os
import yaml
import logging
from typing import Dict, List
from datetime import datetime

class Repository:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.connections: Dict[str, dict] = {}
        self.test_users = self.load_test_users()

    def load_test_users(self) -> List[dict]:
        """Load test users from configuration file"""
        config_path = os.getenv('CONFIG_PATH', '../config/users.yaml')
        try:
            with open(config_path) as f:
                users = yaml.safe_load(f)
                self.logger.info(f"Loaded {len(users)} test users from configuration")
                return users
        except Exception as e:
            self.logger.error(f"Failed to load test users: {e}")
            return []

    def store_connection_data(self, connection_token: str, test_user: dict):
        """Store connection data"""
        self.connections[connection_token] = {
            "connection": {
                "connection_token": connection_token,
                "date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z"),
                "plugin": "social_login",
            },
            "user": {
                "user_token": test_user["user_token"],
                "identity": {
                    "identity_token": test_user["identity_token"],
                    "provider": test_user["provider"],
                    "displayName": test_user["display_name"],
                    "emails": [{"value": test_user["email"]}],
                    "accounts": [{
                        "domain": "test.example.com",
                        "userid": test_user["id"],
                        "username": test_user["username"]
                    }]
                }
            }
        }
        self.logger.info(f"Created connection {connection_token} for test user {test_user['username']}")
        self.logger.info(f"Connection details: {self.connections[connection_token]}")

    def get_connection(self, connection_token: str) -> dict:
        """Retrieve connection details"""
        return self.connections.get(connection_token)

    def list_connections(self) -> List[dict]:
        """List all connections"""
        return list(self.connections.items())
