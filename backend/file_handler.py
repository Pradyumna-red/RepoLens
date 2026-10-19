"""
File handling utilities for ZIP extraction and Python file discovery.
Safely extracts ZIP files and filters Python files.
"""

import os
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import List, Dict
from fastapi import UploadFile, HTTPException
from security import is_safe_path, sanitize_filename, MAX_UNCOMPRESSED_SIZE, MAX_ZIP_ENTRIES


def extract_zip_safely(file: UploadFile, extract_to: str) -> None:
    """
    Safely extract ZIP file to a temporary directory.
    Validates each file path to prevent path traversal attacks.
    Enforces limits on uncompressed size and entry count to prevent ZIP bombs.

    Args:
        file: The uploaded ZIP file
        extract_to: Directory to extract files to

    Raises:
        HTTPException: If ZIP is corrupted, contains unsafe paths, or exceeds limits
    """
    try:
        # Save uploaded file to temporary location
        temp_zip_path = os.path.join(extract_to, "upload.zip")

        with open(temp_zip_path, "wb") as temp_zip:
            shutil.copyfileobj(file.file, temp_zip)

        # Extract ZIP file
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            # Step 1: Pre-extraction validation - check ZIP metadata
            file_list = zip_ref.infolist()

            # Count non-directory entries
            file_entries = [f for f in file_list if not f.is_dir()]

            # Check entry count limit (prevents million-file DoS)
            if len(file_entries) > MAX_ZIP_ENTRIES:
                raise HTTPException(
                    status_code=400,
                    detail=f"ZIP contains too many files ({len(file_entries)}). Maximum allowed: {MAX_ZIP_ENTRIES}"
                )

            # Check declared uncompressed size
            total_uncompressed = sum(f.file_size for f in file_entries)
            if total_uncompressed > MAX_UNCOMPRESSED_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"ZIP uncompressed size ({total_uncompressed / (1024 * 1024):.2f}MB) exceeds limit ({MAX_UNCOMPRESSED_SIZE / (1024 * 1024):.0f}MB)"
                )

            # Step 2: Extract with per-file validation and size tracking
            total_extracted = 0

            for zip_info in file_list:
                # Skip directories
                if zip_info.is_dir():
                    continue

                # Check for path traversal BEFORE sanitizing (to reject malicious ZIPs)
                if not is_safe_path(extract_to, zip_info.filename):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsafe file path detected: {zip_info.filename}"
                    )

                # Sanitize filename for additional safety
                sanitized_name = sanitize_filename(zip_info.filename)

                # Extract individual file
                zip_info.filename = sanitized_name
                zip_ref.extract(zip_info, extract_to)

                # Track actual extracted size (defense in depth - handles lying metadata)
                extracted_path = os.path.join(extract_to, sanitized_name)
                if os.path.isfile(extracted_path):
                    actual_size = os.path.getsize(extracted_path)
                    total_extracted += actual_size

                    # Abort if actual extraction exceeds limit
                    if total_extracted > MAX_UNCOMPRESSED_SIZE:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Extraction aborted: actual uncompressed size exceeds {MAX_UNCOMPRESSED_SIZE / (1024 * 1024):.0f}MB limit"
                        )

        # Remove temporary ZIP file
        os.remove(temp_zip_path)

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors) without wrapping
        raise

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=422,
            detail="Corrupted ZIP file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract ZIP file: {str(e)}"
        )


def find_python_files(directory: str) -> List[Dict[str, str]]:
    """
    Recursively find all Python (.py) files in a directory.

    Args:
        directory: Root directory to search

    Returns:
        List of dictionaries containing file information:
        [{"path": "relative/path/to/file.py", "name": "file.py"}, ...]
    """
    python_files = []
    base_path = Path(directory)

    # Walk through directory tree
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Check if file is a Python file
            if file.endswith('.py'):
                full_path = Path(root) / file

                # Get relative path from base directory
                try:
                    relative_path = full_path.relative_to(base_path)
                except ValueError:
                    # If relative path fails, use full path
                    relative_path = full_path

                python_files.append({
                    "path": str(relative_path).replace('\\', '/'),  # Normalize path separators
                    "name": file
                })

    return python_files


def create_temp_directory() -> str:
    """
    Create a temporary directory for file extraction.

    Returns:
        str: Path to the temporary directory
    """
    return tempfile.mkdtemp(prefix="repolens_")


def cleanup_temp_directory(directory: str) -> None:
    """
    Remove temporary directory and all its contents.

    Args:
        directory: Path to directory to remove
    """
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    except Exception as e:
        # Log error but don't raise - cleanup failure shouldn't break the request
        print(f"Warning: Failed to cleanup temporary directory {directory}: {e}")
