"""
Security validation functions for file uploads.
Ensures uploaded files meet size and type requirements.
"""

import os
from pathlib import Path
from fastapi import UploadFile, HTTPException

# Maximum file size: 50MB (compressed)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes

# Maximum total uncompressed size: 500MB
# Rationale: Allows 10x expansion which is reasonable for Python projects
# with typical compression ratios, while preventing ZIP bombs
MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024  # 500MB in bytes

# Maximum number of files in ZIP: 10,000
# Rationale: Sufficient for large Python projects, prevents resource
# exhaustion from ZIPs with millions of tiny files
MAX_ZIP_ENTRIES = 10000

# ZIP file magic bytes (used to verify it's actually a ZIP file)
ZIP_MAGIC_BYTES = [
    b'PK\x03\x04',  # Local file header
    b'PK\x05\x06',  # Empty archive
    b'PK\x07\x08',  # Spanned archive
]


def validate_file_size(file: UploadFile) -> None:
    """
    Validate that uploaded file does not exceed size limit.

    Args:
        file: The uploaded file to validate

    Raises:
        HTTPException: If file exceeds MAX_FILE_SIZE
    """
    # Seek to end of file to get size
    file.file.seek(0, 2)  # 2 means SEEK_END
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds 50MB limit. Your file: {file_size / (1024 * 1024):.2f}MB"
        )


def validate_zip_file(file: UploadFile) -> None:
    """
    Validate that uploaded file is actually a ZIP file.
    Checks magic bytes, not just file extension.

    Args:
        file: The uploaded file to validate

    Raises:
        HTTPException: If file is not a valid ZIP file
    """
    # Read first 4 bytes to check magic number
    file.file.seek(0)
    magic_bytes = file.file.read(4)
    file.file.seek(0)  # Reset to beginning

    # Check if matches any valid ZIP magic bytes
    is_zip = any(magic_bytes.startswith(magic) for magic in ZIP_MAGIC_BYTES)

    if not is_zip:
        raise HTTPException(
            status_code=422,
            detail="Not a valid ZIP file"
        )


def is_safe_path(base_dir: str, file_path: str) -> bool:
    """
    Check if a file path is safe (doesn't escape base directory).
    Prevents path traversal attacks like ../../etc/passwd

    Args:
        base_dir: The base directory that should contain the file
        file_path: The file path to validate

    Returns:
        bool: True if path is safe, False otherwise
    """
    try:
        base = Path(base_dir).resolve()
        target = Path(base_dir, file_path).resolve()

        # Check if target is inside base directory
        return base == target or base in target.parents
    except (ValueError, OSError):
        # If resolution fails, it's not safe
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing dangerous characters.

    Args:
        filename: The filename to sanitize

    Returns:
        str: Sanitized filename
    """
    # Remove null bytes
    sanitized = filename.replace('\0', '')

    # Remove .. sequences (path traversal)
    while '..' in sanitized:
        sanitized = sanitized.replace('..', '')

    # Remove leading slashes
    sanitized = sanitized.lstrip('/')
    sanitized = sanitized.lstrip('\\')

    return sanitized
