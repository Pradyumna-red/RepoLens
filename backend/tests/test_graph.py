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


def test_package_and_relative_cycles_resolve_to_project_files(tmp_path):
    files = write_project(
        tmp_path,
        {
            "pkg/__init__.py": "",
            "pkg/a.py": "from . import b\n",
            "pkg/b.py": "from pkg import a\n",
        },
    )

    result = build_dependency_graph(files, str(tmp_path))

    assert result["graph"]["pkg/a.py"] == ["pkg/b.py"]
    assert result["graph"]["pkg/b.py"] == ["pkg/a.py"]


def test_wrapped_project_imports_resolve_without_wrapper_package(tmp_path):
    files = write_project(
        tmp_path,
        {
            "django-ecommerce-master/djecommerce/__init__.py": "",
            "django-ecommerce-master/djecommerce/urls.py": (
                "from djecommerce.wsgi import application\n"
            ),
            "django-ecommerce-master/djecommerce/wsgi.py": (
                "from djecommerce.urls import urlpatterns\n"
            ),
            "django-ecommerce-master/core/__init__.py": "",
            "django-ecommerce-master/core/models.py": "",
        },
    )

    result = build_dependency_graph(files, str(tmp_path))

    assert result["graph"] == {
        "django-ecommerce-master/core/__init__.py": [],
        "django-ecommerce-master/core/models.py": [],
        "django-ecommerce-master/djecommerce/__init__.py": [],
        "django-ecommerce-master/djecommerce/urls.py": [
            "django-ecommerce-master/djecommerce/wsgi.py",
        ],
        "django-ecommerce-master/djecommerce/wsgi.py": [
            "django-ecommerce-master/djecommerce/urls.py",
        ],
    }


def test_unwrapped_project_imports_still_resolve(tmp_path):
    files = write_project(
        tmp_path,
        {
            "core/__init__.py": "",
            "core/models.py": "",
            "main.py": "from core import models\n",
        },
    )

    result = build_dependency_graph(files, str(tmp_path))

    assert result["graph"]["main.py"] == ["core/models.py"]


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
