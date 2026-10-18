"""
RepoLens Backend - FastAPI Application
Main entry point for the Python codebase analyzer API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI application instance
app = FastAPI(
    title="RepoLens API",
    description="Python codebase analyzer - analyzes imports and dependency graphs",
    version="1.0.0"
)

# Configure CORS to allow frontend requests
# This allows the React app running on localhost:5173 to call our API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",  # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.

    Returns:
        dict: Status and version information
    """
    return {
        "status": "ok",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """
    Root endpoint - provides basic API information.

    Returns:
        dict: Welcome message and documentation link
    """
    return {
        "message": "RepoLens API - Python Codebase Analyzer",
        "docs": "/docs",
        "health": "/api/health"
    }
