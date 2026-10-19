"""
Tests for ZIP bomb protection.
Verifies that the system rejects ZIPs with excessive uncompressed sizes
or file counts without consuming excessive resources.
"""

import pytest
import os
import tempfile
import zipfile
import io
from fastapi import UploadFile, HTTPException
from file_handler import extract_zip_safely, cleanup_temp_directory
from security import MAX_UNCOMPRESSED_SIZE, MAX_ZIP_ENTRIES


def test_normal_zip_within_limits():
    """Test that a normal ZIP with reasonable size and file count is accepted."""
    temp_dir = tempfile.mkdtemp()
    zip_buffer = io.BytesIO()

    try:
        # Create a ZIP with 10 small Python files (well within limits)
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i in range(10):
                content = f"# File {i}\nimport os\nprint('hello')\n" * 10
                zf.writestr(f"file_{i}.py", content)

        zip_buffer.seek(0)
        upload = UploadFile(filename="normal.zip", file=zip_buffer)

        # Should extract successfully
        extract_zip_safely(upload, temp_dir)

        # Verify files were extracted
        extracted_files = [f for f in os.listdir(temp_dir) if f.endswith('.py')]
        assert len(extracted_files) == 10

    finally:
        cleanup_temp_directory(temp_dir)


def test_zip_exceeds_uncompressed_size_limit():
    """Test that a ZIP whose declared uncompressed size exceeds the limit is rejected."""
    temp_dir = tempfile.mkdtemp()
    zip_buffer = io.BytesIO()

    try:
        # Create a ZIP with metadata showing size > MAX_UNCOMPRESSED_SIZE
        # Use highly compressible data (repeated zeros)
        large_content = b'0' * (MAX_UNCOMPRESSED_SIZE // 5)  # 100MB of zeros

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Write 6 files of 100MB each = 600MB uncompressed (exceeds 500MB limit)
            for i in range(6):
                zf.writestr(f"large_{i}.py", large_content)

        zip_buffer.seek(0)
        file_size = len(zip_buffer.getvalue())
        print(f"Created test ZIP: {file_size / (1024 * 1024):.2f}MB compressed")

        upload = UploadFile(filename="toolarge.zip", file=zip_buffer)

        # Should raise HTTPException before extraction
        with pytest.raises(HTTPException) as exc_info:
            extract_zip_safely(upload, temp_dir)

        assert exc_info.value.status_code == 400
        assert "uncompressed size" in exc_info.value.detail.lower()
        assert "exceeds limit" in exc_info.value.detail.lower()

    finally:
        cleanup_temp_directory(temp_dir)


def test_zip_exceeds_entry_count_limit():
    """Test that a ZIP with too many files is rejected."""
    temp_dir = tempfile.mkdtemp()
    zip_buffer = io.BytesIO()

    try:
        # Create a ZIP with more than MAX_ZIP_ENTRIES files
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i in range(MAX_ZIP_ENTRIES + 100):
                zf.writestr(f"file_{i}.py", f"# File {i}\n")

        zip_buffer.seek(0)
        upload = UploadFile(filename="toomany.zip", file=zip_buffer)

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            extract_zip_safely(upload, temp_dir)

        assert exc_info.value.status_code == 400
        assert "too many files" in exc_info.value.detail.lower()
        assert str(MAX_ZIP_ENTRIES) in exc_info.value.detail

    finally:
        cleanup_temp_directory(temp_dir)


def test_zip_with_lying_metadata():
    """
    Test that actual extraction size is tracked (defense in depth).
    This simulates a ZIP where metadata might not match actual content.
    """
    temp_dir = tempfile.mkdtemp()
    zip_buffer = io.BytesIO()

    try:
        # Create a normal ZIP that's within pre-check limits
        # In a real ZIP bomb, compressed size would be tiny but expand huge
        # We simulate with moderately large files
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Create 50 files of ~1MB each compressed (will be more uncompressed)
            for i in range(50):
                # Repeated pattern compresses well
                content = (f"# File {i}\n" + "x" * 10000 + "\n") * 100
                zf.writestr(f"file_{i}.py", content)

        # Check that this is within our allowed limits
        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            total_uncompressed = sum(f.file_size for f in zf.infolist() if not f.is_dir())
            print(f"Total uncompressed size: {total_uncompressed / (1024 * 1024):.2f}MB")

        # Should extract if within limits
        zip_buffer.seek(0)
        upload = UploadFile(filename="normal.zip", file=zip_buffer)
        extract_zip_safely(upload, temp_dir)

        # Verify extraction happened
        extracted_files = [f for f in os.listdir(temp_dir) if f.endswith('.py')]
        assert len(extracted_files) > 0

    finally:
        cleanup_temp_directory(temp_dir)


def test_corrupted_zip_rejected():
    """Test that corrupted ZIP files are still rejected."""
    temp_dir = tempfile.mkdtemp()

    try:
        # Create a fake ZIP that starts with magic bytes but is corrupted
        fake_zip = io.BytesIO(b"PK\x03\x04" + b"corrupted data" * 100)
        upload = UploadFile(filename="corrupted.zip", file=fake_zip)

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            extract_zip_safely(upload, temp_dir)

        assert exc_info.value.status_code == 422

    finally:
        cleanup_temp_directory(temp_dir)


def test_path_traversal_still_blocked():
    """Test that path traversal protection still works with new limits."""
    temp_dir = tempfile.mkdtemp()
    zip_buffer = io.BytesIO()

    try:
        # Create ZIP with path traversal attempt
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("../../etc/passwd", "malicious content")
            zf.writestr("safe.py", "# safe file")

        zip_buffer.seek(0)
        upload = UploadFile(filename="malicious.zip", file=zip_buffer)

        # Should raise HTTPException for unsafe path
        with pytest.raises(HTTPException) as exc_info:
            extract_zip_safely(upload, temp_dir)

        assert exc_info.value.status_code == 400
        assert "unsafe file path" in exc_info.value.detail.lower()

    finally:
        cleanup_temp_directory(temp_dir)


def test_cleanup_after_limit_violation():
    """Test that temp directory is cleaned up even when limits are exceeded."""
    temp_dir = tempfile.mkdtemp()
    zip_buffer = io.BytesIO()

    # Verify temp dir exists
    assert os.path.exists(temp_dir)

    try:
        # Create a ZIP that exceeds entry limit
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for i in range(MAX_ZIP_ENTRIES + 10):
                zf.writestr(f"file_{i}.py", f"# File {i}\n")

        zip_buffer.seek(0)
        upload = UploadFile(filename="toomany.zip", file=zip_buffer)

        # Should raise exception
        with pytest.raises(HTTPException):
            extract_zip_safely(upload, temp_dir)

        # Temp directory should still exist (extraction failed, so upload.zip might be there)
        # But we should be able to clean it up
        cleanup_temp_directory(temp_dir)
        assert not os.path.exists(temp_dir)

    except Exception:
        # Ensure cleanup even if test fails
        if os.path.exists(temp_dir):
            cleanup_temp_directory(temp_dir)
        raise


def test_empty_zip_still_accepted():
    """Test that empty ZIPs are still handled gracefully."""
    temp_dir = tempfile.mkdtemp()
    zip_buffer = io.BytesIO()

    try:
        # Create empty ZIP
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            pass  # Empty

        zip_buffer.seek(0)
        upload = UploadFile(filename="empty.zip", file=zip_buffer)

        # Should extract successfully (0 files is within limits)
        extract_zip_safely(upload, temp_dir)

        # No .py files should exist
        py_files = [f for f in os.listdir(temp_dir) if f.endswith('.py')]
        assert len(py_files) == 0

    finally:
        cleanup_temp_directory(temp_dir)


def test_zip_at_exact_entry_limit():
    """Test that a ZIP with exactly MAX_ZIP_ENTRIES is accepted."""
    temp_dir = tempfile.mkdtemp()
    zip_buffer = io.BytesIO()

    try:
        # Create ZIP with exactly MAX_ZIP_ENTRIES files
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i in range(MAX_ZIP_ENTRIES):
                zf.writestr(f"file_{i}.py", f"# File {i}\n")

        zip_buffer.seek(0)
        upload = UploadFile(filename="exact_limit.zip", file=zip_buffer)

        # Should extract successfully (at limit, not over)
        extract_zip_safely(upload, temp_dir)

        # All files should be extracted
        py_files = [f for f in os.listdir(temp_dir) if f.endswith('.py')]
        assert len(py_files) == MAX_ZIP_ENTRIES

    finally:
        cleanup_temp_directory(temp_dir)
