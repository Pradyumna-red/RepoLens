"""Tests for Milestone 5 dependency graph construction."""

from pathlib import Path

from analyzer import build_dependency_graph


def write_project(root: Path, files: dict[str, str]) -> list[dict[str, str]]:
    """Create a project fixture and return file metadata like file_handler."""
    metadata = []
    for relative_path, source in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        metadata.append({"path": relative_path, "name": path.name})
    return metadata


def test_build_dependency_graph_and_reverse_mapping(tmp_path):
    files = write_project(
        tmp_path,
        {
            "main.py": "import utils\nimport config\n",
            "utils.py": "import helpers\n",
            "config.py": "",
            "helpers.py": "",
        },
    )

    result = build_dependency_graph(files, str(tmp_path))

    assert result["graph"] == {
        "config.py": [],
        "helpers.py": [],
        "main.py": ["config.py", "utils.py"],
        "utils.py": ["helpers.py"],
    }
    assert result["imported_by"] == {
        "config.py": ["main.py"],
        "helpers.py": ["utils.py"],
        "main.py": [],
        "utils.py": ["main.py"],
    }
    assert result["import_counts"] == {
        "config.py": 0,
        "helpers.py": 0,
        "main.py": 2,
        "utils.py": 1,
    }


def test_unresolved_imports_do_not_create_edges(tmp_path):
    files = write_project(
        tmp_path,
        {
            "main.py": "import os\nimport missing_package\n",
            "leaf.py": "",
        },
    )

    result = build_dependency_graph(files, str(tmp_path))

    assert result["graph"] == {"leaf.py": [], "main.py": []}
    assert result["imported_by"] == {"leaf.py": [], "main.py": []}
    assert result["unresolved_imports"]["main.py"] == ["missing_package", "os"]


def test_relative_and_from_imports_resolve_to_project_files(tmp_path):
    files = write_project(
        tmp_path,
        {
            "pkg/__init__.py": "",
            "pkg/main.py": "from . import helpers\nfrom .config import VALUE\n",
            "pkg/helpers.py": "",
            "pkg/config.py": "",
        },
    )

    result = build_dependency_graph(files, str(tmp_path))

    assert result["graph"]["pkg/main.py"] == [
        "pkg/config.py",
        "pkg/helpers.py",
    ]
    assert result["imported_by"]["pkg/config.py"] == ["pkg/main.py"]
    assert result["imported_by"]["pkg/helpers.py"] == ["pkg/main.py"]


def test_duplicate_imports_and_syntax_errors_are_safe(tmp_path):
    files = write_project(
        tmp_path,
        {
            "main.py": "import leaf\nimport leaf\n",
            "leaf.py": "",
            "broken.py": "def invalid syntax(:\n",
        },
    )

    result = build_dependency_graph(files, str(tmp_path))

    assert result["graph"]["main.py"] == ["leaf.py"]
    assert result["graph"]["broken.py"] == []
    assert set(result["graph"]) == {"broken.py", "leaf.py", "main.py"}
