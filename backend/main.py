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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Design System Extractor API", "status": "running"}


# Fix: Add health check at BOTH /health and /api/health to match frontend expectations
@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
