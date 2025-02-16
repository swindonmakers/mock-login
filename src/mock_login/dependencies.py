import logging

from .repository import Repository
from .service import AuthService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
repository = Repository(logger=logger)
auth_service = AuthService(repository=repository, logger=logger)

# Dependency injection
async def get_repository():
    return repository

async def get_auth_service():
    return auth_service

async def get_logger():
    return logger
