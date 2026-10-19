"""
Tests for file handling functions.
"""

import pytest
import os
import tempfile
import zipfile
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
import io
from file_handler import (
    extract_zip_safely,
    find_python_files,
    create_temp_directory,
    cleanup_temp_directory
)


def create_test_zip_with_python_files():
    """Helper function to create a test ZIP with Python files."""
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "test.zip")

    # Create some test Python files in a temporary structure
    test_structure = {
        "main.py": "import os",
        "utils.py": "def helper(): pass",
        "subdir/module.py": "# A module",
    }

    with zipfile.ZipFile(zip_path, 'w') as zf:
        for file_path, content in test_structure.items():
            zf.writestr(file_path, content)

    return zip_path, temp_dir


def create_malicious_zip():
    """Helper function to create a ZIP with path traversal attempt."""
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "malicious.zip")

    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Try to escape with ../
        zf.writestr("../../etc/passwd", "malicious content")
        zf.writestr("safe.py", "# safe file")

    return zip_path, temp_dir


def test_create_temp_directory():
    """Test that temporary directory is created."""
    temp_dir = create_temp_directory()

    assert os.path.exists(temp_dir)
    assert "repolens_" in temp_dir

    # Cleanup
    cleanup_temp_directory(temp_dir)


def test_cleanup_temp_directory():
    """Test that temporary directory is removed."""
    temp_dir = create_temp_directory()

    # Create a file inside
    test_file = os.path.join(temp_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("test")

    # Cleanup
    cleanup_temp_directory(temp_dir)

    assert not os.path.exists(temp_dir)


def test_extract_zip_safely_with_valid_zip():
    """Test extracting a valid ZIP file."""
    zip_path, zip_temp_dir = create_test_zip_with_python_files()
    extract_dir = tempfile.mkdtemp()

    try:
        # Open as UploadFile
        with open(zip_path, "rb") as f:
            upload = UploadFile(filename="test.zip", file=f)
            extract_zip_safely(upload, extract_dir)

        # Check files were extracted
        assert os.path.exists(os.path.join(extract_dir, "main.py"))
        assert os.path.exists(os.path.join(extract_dir, "utils.py"))
        assert os.path.exists(os.path.join(extract_dir, "subdir", "module.py"))

    finally:
        cleanup_temp_directory(extract_dir)
        cleanup_temp_directory(zip_temp_dir)


def test_extract_zip_safely_rejects_path_traversal():
    """Test that path traversal attempts are caught."""
    zip_path, zip_temp_dir = create_malicious_zip()
    extract_dir = tempfile.mkdtemp()

    try:
        with open(zip_path, "rb") as f:
            upload = UploadFile(filename="malicious.zip", file=f)

            # Should raise HTTPException for unsafe path
            with pytest.raises(HTTPException) as exc_info:
                extract_zip_safely(upload, extract_dir)

            assert exc_info.value.status_code == 400
            assert "Unsafe file path" in exc_info.value.detail

    finally:
        cleanup_temp_directory(extract_dir)
        cleanup_temp_directory(zip_temp_dir)


def test_extract_zip_safely_rejects_corrupted_zip():
    """Test that corrupted ZIP files are rejected."""
    extract_dir = tempfile.mkdtemp()

    try:
        # Create a fake ZIP that's not actually valid
        fake_zip = io.BytesIO(b"PK\x03\x04" + b"corrupted data")
        upload = UploadFile(filename="corrupted.zip", file=fake_zip)

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            extract_zip_safely(upload, extract_dir)

        assert exc_info.value.status_code == 422

    finally:
        cleanup_temp_directory(extract_dir)


def test_find_python_files():
    """Test finding Python files in a directory."""
    temp_dir = tempfile.mkdtemp()

    try:
        # Create test structure
        os.makedirs(os.path.join(temp_dir, "subdir"))
        open(os.path.join(temp_dir, "main.py"), "w").close()
        open(os.path.join(temp_dir, "utils.py"), "w").close()
        open(os.path.join(temp_dir, "subdir", "module.py"), "w").close()
        open(os.path.join(temp_dir, "readme.txt"), "w").close()  # Not Python

        # Find Python files
        python_files = find_python_files(temp_dir)

        # Should find 3 Python files
        assert len(python_files) == 3

        # Check file names
        names = [f["name"] for f in python_files]
        assert "main.py" in names
        assert "utils.py" in names
        assert "module.py" in names

        # Should not include .txt file
        assert "readme.txt" not in names

    finally:
        cleanup_temp_directory(temp_dir)


def test_find_python_files_empty_directory():
    """Test finding Python files in an empty directory."""
    temp_dir = tempfile.mkdtemp()

    try:
        python_files = find_python_files(temp_dir)
        assert len(python_files) == 0

    finally:
        cleanup_temp_directory(temp_dir)
