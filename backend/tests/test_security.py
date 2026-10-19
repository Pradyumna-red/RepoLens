"""
Tests for security validation functions.
"""

import pytest
import io
from fastapi import UploadFile, HTTPException
from security import (
    validate_file_size,
    validate_zip_file,
    is_safe_path,
    sanitize_filename,
    MAX_FILE_SIZE
)


def test_validate_file_size_accepts_small_file():
    """Test that files under 50MB are accepted."""
    # Create a small file (1KB)
    small_file = io.BytesIO(b"x" * 1024)
    upload = UploadFile(filename="test.zip", file=small_file)

    # Should not raise exception
    validate_file_size(upload)


def test_validate_file_size_rejects_large_file():
    """Test that files over 50MB are rejected."""
    # Create a file that's over 50MB
    large_file = io.BytesIO(b"x" * (MAX_FILE_SIZE + 1))
    upload = UploadFile(filename="large.zip", file=large_file)

    # Should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        validate_file_size(upload)

    assert exc_info.value.status_code == 400
    assert "exceeds 50MB limit" in exc_info.value.detail


def test_validate_zip_file_accepts_valid_zip():
    """Test that valid ZIP files are accepted."""
    # ZIP magic bytes: PK\x03\x04
    zip_content = b'PK\x03\x04' + b'\x00' * 100
    zip_file = io.BytesIO(zip_content)
    upload = UploadFile(filename="test.zip", file=zip_file)

    # Should not raise exception
    validate_zip_file(upload)


def test_validate_zip_file_rejects_non_zip():
    """Test that non-ZIP files are rejected."""
    # Not a ZIP file
    text_file = io.BytesIO(b"This is just text, not a ZIP")
    upload = UploadFile(filename="fake.zip", file=text_file)

    # Should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        validate_zip_file(upload)

    assert exc_info.value.status_code == 422
    assert "Not a valid ZIP file" in exc_info.value.detail


def test_is_safe_path_accepts_safe_paths():
    """Test that safe paths within base directory are accepted."""
    base = "/tmp/test"

    assert is_safe_path(base, "file.py") is True
    assert is_safe_path(base, "subdir/file.py") is True
    assert is_safe_path(base, "a/b/c/file.py") is True


def test_is_safe_path_rejects_traversal_attacks():
    """Test that path traversal attempts are rejected."""
    base = "/tmp/test"

    assert is_safe_path(base, "../etc/passwd") is False
    assert is_safe_path(base, "../../etc/passwd") is False
    assert is_safe_path(base, "subdir/../../etc/passwd") is False


def test_sanitize_filename_removes_dangerous_chars():
    """Test that dangerous characters are removed from filenames."""
    assert sanitize_filename("file.py") == "file.py"
    assert sanitize_filename("../file.py") == "file.py"
    assert sanitize_filename("../../etc/passwd") == "etc/passwd"
    assert sanitize_filename("file\x00.py") == "file.py"
