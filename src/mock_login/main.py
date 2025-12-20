import importlib.metadata
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import oneall, testapp, main

try:
    __version__ = importlib.metadata.version("mock-login")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

app = FastAPI(
    title="Mock OneAll Service",
    version=__version__,
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(main.router)
app.include_router(oneall.router)
app.include_router(testapp.router)
