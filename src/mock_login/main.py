from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import oneall, testapp, main


app = FastAPI(
    title="Mock OneAll Service",
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
