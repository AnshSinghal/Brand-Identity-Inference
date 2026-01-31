"""
Design System Extractor - Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Design System Extractor",
    description="Extract visual identity from any website",
    version="1.0.0"
)

# CORS for frontend
# We disable allow_credentials=True because we use allow_origins=["*"]
# This is safer for public APIs and prevents browser blocking.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Changed to False to allow wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Design System Extractor API", "status": "running"}


# Health checks at both paths
@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
