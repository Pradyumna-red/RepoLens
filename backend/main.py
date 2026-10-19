"""
RepoLens Backend - FastAPI Application
Main entry point for the Python codebase analyzer API
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import os
import security
import file_handler
import analyzer
from models import AnalysisResponse

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


@app.post("/api/analyze")
async def analyze_project(file: UploadFile = File(...)):
    """
    Analyze a Python project ZIP file.
    Extracts the ZIP, finds all Python files, analyzes imports using AST.

    Args:
        file: Uploaded ZIP file containing Python project

    Returns:
        dict: Analysis results with list of Python files and their imports

    Raises:
        HTTPException: If file validation fails or extraction errors occur
    """
    temp_dir = None

    try:
        # Step 1: Validate file size (50MB limit)
        security.validate_file_size(file)

        # Step 2: Validate file is actually a ZIP
        security.validate_zip_file(file)

        # Step 3: Create temporary directory for extraction
        temp_dir = file_handler.create_temp_directory()

        # Step 4: Extract ZIP safely (with path traversal protection)
        file_handler.extract_zip_safely(file, temp_dir)

        # Step 5: Find all Python files
        python_files = file_handler.find_python_files(temp_dir)

        # Step 6: Analyze each Python file for imports (NEW in Milestone 4)
        analyzed_files = []
        for py_file in python_files:
            file_full_path = os.path.join(temp_dir, py_file['path'])

            # Parse imports using AST
            import_data = analyzer.parse_imports(file_full_path, temp_dir)

            analyzed_files.append({
                'path': py_file['path'],
                'name': py_file['name'],
                'imports': import_data['imports'],
                'from_imports': import_data['from_imports'],
                'import_count': len(import_data['imports']) + len(import_data['from_imports'])
            })

        # Step 7: Build project dependency and reverse-dependency mappings
        dependency_data = analyzer.build_dependency_graph(python_files, temp_dir)

        # Step 8: Return legacy import data plus additive graph information
        total_imports = sum(f['import_count'] for f in analyzed_files)
        response = AnalysisResponse(
            message="Analysis complete",
            project_name=file.filename.replace('.zip', ''),
            total_files=len(analyzed_files),
            total_imports=total_imports,
            files=analyzed_files,
            dependency_graph=dependency_data['graph'],
            imported_by=dependency_data['imported_by'],
            import_counts=dependency_data['import_counts'],
            unresolved_imports=dependency_data['unresolved_imports']
        )

        return response.model_dump()

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise

    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

    finally:
        # Step 8: Always cleanup temporary directory
        if temp_dir:
            file_handler.cleanup_temp_directory(temp_dir)
