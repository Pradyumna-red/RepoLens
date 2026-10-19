"""
Tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import zipfile
import io
import tempfile
import os
from main import app

client = TestClient(app)


def create_valid_test_zip():
    """Create a valid ZIP file with Python files for testing."""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("main.py", "import os\nimport sys")
        zf.writestr("utils.py", "def helper():\n    pass")
        zf.writestr("subdir/module.py", "# Module file")

    zip_buffer.seek(0)
    return zip_buffer


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "RepoLens API" in data["message"]


def test_analyze_with_valid_zip():
    """Test analyzing a valid ZIP file."""
    zip_file = create_valid_test_zip()

    response = client.post(
        "/api/analyze",
        files={"file": ("test.zip", zip_file, "application/zip")}
    )

    assert response.status_code == 200
    data = response.json()

    assert "files" in data
    assert data["total_files"] == 3
    assert data["project_name"] == "test"

    # Check that Python files were found
    file_names = [f["name"] for f in data["files"]]
    assert "main.py" in file_names
    assert "utils.py" in file_names
    assert "module.py" in file_names


def test_analyze_returns_dependency_graph():
    """Test that analysis retains legacy fields and adds graph data."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("main.py", "import utils\nimport config\n")
        zf.writestr("utils.py", "import helpers\n")
        zf.writestr("config.py", "")
        zf.writestr("helpers.py", "")
    zip_buffer.seek(0)

    response = client.post(
        "/api/analyze",
        files={"file": ("graph.zip", zip_buffer, "application/zip")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 4
    assert data["total_imports"] == 3
    assert data["dependency_graph"]["main.py"] == ["config.py", "utils.py"]
    assert data["dependency_graph"]["utils.py"] == ["helpers.py"]
    assert data["imported_by"]["config.py"] == ["main.py"]
    assert data["import_counts"]["main.py"] == 2
    assert data["circular_imports"] == []
    assert data["files"]


def test_analyze_returns_circular_imports():
    """Test that API responses include formatted cycle information."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("a.py", "import b\n")
        zf.writestr("b.py", "import c\n")
        zf.writestr("c.py", "import a\n")
    zip_buffer.seek(0)

    response = client.post(
        "/api/analyze",
        files={"file": ("cycle.zip", zip_buffer, "application/zip")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 3
    assert data["dependency_graph"]["a.py"] == ["b.py"]
    assert data["circular_imports"] == [{
        "cycle": ["a.py", "b.py", "c.py", "a.py"],
        "description": "a.py → b.py → c.py → a.py",
    }]


def test_analyze_rejects_oversized_file():
    """Test that files over 50MB are rejected."""
    # Create a large fake file (over 50MB)
    large_content = b"x" * (51 * 1024 * 1024)  # 51MB
    large_file = io.BytesIO(large_content)

    response = client.post(
        "/api/analyze",
        files={"file": ("large.zip", large_file, "application/zip")}
    )

    assert response.status_code == 400
    assert "exceeds 50MB limit" in response.json()["detail"]


def test_analyze_rejects_non_zip():
    """Test that non-ZIP files are rejected."""
    text_file = io.BytesIO(b"This is not a ZIP file")

    response = client.post(
        "/api/analyze",
        files={"file": ("fake.zip", text_file, "application/zip")}
    )

    assert response.status_code == 422
    assert "Not a valid ZIP file" in response.json()["detail"]


def test_analyze_without_file():
    """Test that endpoint requires a file."""
    response = client.post("/api/analyze")

    assert response.status_code == 422  # Validation error
