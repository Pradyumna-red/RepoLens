"""
Tests for the AST-based import analyzer.
"""

import pytest
import os
import tempfile
from pathlib import Path
from analyzer import parse_imports, resolve_relative_import, get_all_imports, analyze_file


def create_temp_python_file(content: str) -> str:
    """Helper function to create a temporary Python file with given content."""
    fd, path = tempfile.mkstemp(suffix='.py')
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return path


def test_parse_simple_imports():
    """Test parsing standard import statements."""
    code = """
import os
import sys
import json
"""
    file_path = create_temp_python_file(code)

    try:
        result = parse_imports(file_path)

        assert 'os' in result['imports']
        assert 'sys' in result['imports']
        assert 'json' in result['imports']
        assert len(result['imports']) == 3
        assert len(result['from_imports']) == 0

    finally:
        os.remove(file_path)


def test_parse_from_imports():
    """Test parsing 'from x import y' statements."""
    code = """
from pathlib import Path
from os.path import join
from typing import List, Dict
"""
    file_path = create_temp_python_file(code)

    try:
        result = parse_imports(file_path)

        assert 'pathlib' in result['from_imports']
        assert 'os.path' in result['from_imports']
        assert 'typing' in result['from_imports']
        assert len(result['from_imports']) == 3
        assert len(result['imports']) == 0

    finally:
        os.remove(file_path)


def test_parse_mixed_imports():
    """Test parsing both import types together."""
    code = """
import os
from pathlib import Path
import sys
from typing import List
"""
    file_path = create_temp_python_file(code)

    try:
        result = parse_imports(file_path)

        assert len(result['imports']) == 2
        assert len(result['from_imports']) == 2
        assert 'os' in result['imports']
        assert 'sys' in result['imports']
        assert 'pathlib' in result['from_imports']
        assert 'typing' in result['from_imports']

    finally:
        os.remove(file_path)


def test_parse_relative_imports_without_project_root():
    """Test that relative imports are captured (even if not resolved)."""
    code = """
from . import helpers
from .. import config
from ...utils import formatter
"""
    file_path = create_temp_python_file(code)

    try:
        result = parse_imports(file_path)

        # Without project root, relative imports are stored as-is
        assert len(result['from_imports']) == 3
        # Check that we captured something for relative imports
        assert any('.' in imp or 'helpers' in imp for imp in result['from_imports'])

    finally:
        os.remove(file_path)


def test_parse_no_imports():
    """Test parsing a file with no imports."""
    code = """
def hello():
    print("Hello, World!")

class MyClass:
    pass
"""
    file_path = create_temp_python_file(code)

    try:
        result = parse_imports(file_path)

        assert len(result['imports']) == 0
        assert len(result['from_imports']) == 0

    finally:
        os.remove(file_path)


def test_parse_file_with_syntax_error():
    """Test that syntax errors don't crash the parser."""
    code = """
import os
def broken syntax here
from pathlib import Path
"""
    file_path = create_temp_python_file(code)

    try:
        result = parse_imports(file_path)

        # Should return empty results, not crash
        assert 'imports' in result
        assert 'from_imports' in result

    finally:
        os.remove(file_path)


def test_get_all_imports():
    """Test getting a flat list of all imports."""
    code = """
import os
import sys
from pathlib import Path
from typing import List
"""
    file_path = create_temp_python_file(code)

    try:
        all_imports = get_all_imports(file_path)

        assert len(all_imports) == 4
        assert 'os' in all_imports
        assert 'sys' in all_imports
        assert 'pathlib' in all_imports
        assert 'typing' in all_imports

    finally:
        os.remove(file_path)


def test_resolve_relative_import():
    """Test resolving relative imports to absolute paths."""
    # Create a temporary project structure
    temp_dir = tempfile.mkdtemp()

    try:
        # Create: project/src/utils/helpers.py
        src_dir = Path(temp_dir) / 'src' / 'utils'
        src_dir.mkdir(parents=True)
        helpers_file = src_dir / 'helpers.py'
        helpers_file.write_text("# helpers")

        # Test: from .. import config (level=2, from src/utils)
        # Should resolve to: src.config
        resolved = resolve_relative_import(
            str(helpers_file),
            'config',
            2,
            temp_dir
        )

        assert resolved == 'src.config'

        # Test: from . import other (level=1, from src/utils)
        # Should resolve to: src.utils.other
        resolved = resolve_relative_import(
            str(helpers_file),
            'other',
            1,
            temp_dir
        )

        assert resolved == 'src.utils.other'

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)


def test_analyze_file():
    """Test the complete file analysis function."""
    code = """
import os
from pathlib import Path
import sys
"""
    file_path = create_temp_python_file(code)

    try:
        result = analyze_file(file_path)

        assert 'file' in result
        assert 'imports' in result
        assert 'from_imports' in result
        assert 'all_imports' in result

        assert len(result['imports']) == 2
        assert len(result['from_imports']) == 1
        assert len(result['all_imports']) == 3

    finally:
        os.remove(file_path)


def test_multiline_imports():
    """Test parsing multiline import statements."""
    code = """
from typing import (
    List,
    Dict,
    Optional
)
import os, sys, json
"""
    file_path = create_temp_python_file(code)

    try:
        result = parse_imports(file_path)

        # Should capture the from import
        assert 'typing' in result['from_imports']

        # Should capture all three imports
        assert 'os' in result['imports']
        assert 'sys' in result['imports']
        assert 'json' in result['imports']

    finally:
        os.remove(file_path)


def test_ignore_non_import_statements():
    """Test that non-import statements are ignored."""
    code = """
import os

def some_function():
    import_like_variable = "not an import"
    return import_like_variable

class MyClass:
    from_value = "also not an import"

# import commented_out
"""
    file_path = create_temp_python_file(code)

    try:
        result = parse_imports(file_path)

        # Should only find the real import
        assert len(result['imports']) == 1
        assert 'os' in result['imports']
        assert len(result['from_imports']) == 0

    finally:
        os.remove(file_path)


def test_parse_bare_relative_import_single():
    """Test parsing a bare relative import with a single alias."""
    code = """
from . import helpers
"""
    file_path = create_temp_python_file(code)

    # Create a temporary project structure to provide project_root
    temp_dir = tempfile.mkdtemp()
    try:
        # Create: project/src/utils/helpers.py
        src_dir = Path(temp_dir) / 'src' / 'utils'
        src_dir.mkdir(parents=True)
        helpers_file = src_dir / 'helpers.py'
        helpers_file.write_text(code)

        # Set project_root to the temp_dir
        project_root = str(temp_dir)

        result = parse_imports(str(helpers_file), project_root)

        # Expect: from_imports contains the resolved module for the alias
        assert len(result['from_imports']) == 1
        assert 'src.utils.helpers' in result['from_imports']
        assert len(result['imports']) == 0

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        os.remove(file_path)


def test_parse_bare_relative_import_multiple():
    """Test parsing a bare relative import with multiple aliases."""
    code = """
from . import a, b
"""
    file_path = create_temp_python_file(code)

    # Create a temporary project structure to provide project_root
    temp_dir = tempfile.mkdtemp()
    try:
        # Create: project/src/utils/helpers.py
        src_dir = Path(temp_dir) / 'src' / 'utils'
        src_dir.mkdir(parents=True)
        helpers_file = src_dir / 'helpers.py'
        helpers_file.write_text(code)

        # Set project_root to the temp_dir
        project_root = str(temp_dir)

        result = parse_imports(str(helpers_file), project_root)

        # Expect: from_imports contains the resolved modules for each alias
        assert len(result['from_imports']) == 2
        assert 'src.utils.a' in result['from_imports']
        assert 'src.utils.b' in result['from_imports']
        assert len(result['imports']) == 0

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        os.remove(file_path)


def test_parse_relative_import_with_module():
    """Test parsing a relative import with a module component (e.g., from ..subpackage import module)."""
    code = """
from ..subpackage import module
"""
    file_path = create_temp_python_file(code)

    # Create a temporary project structure to provide project_root
    temp_dir = tempfile.mkdtemp()
    try:
        # Create: project/src/utils/helpers.py
        src_dir = Path(temp_dir) / 'src' / 'utils'
        src_dir.mkdir(parents=True)
        helpers_file = src_dir / 'helpers.py'
        helpers_file.write_text(code)

        # Also create the subpackage directory (as a sibling to utils) for the import to be resolvable
        subpackage_dir = Path(temp_dir) / 'src' / 'subpackage'
        subpackage_dir.mkdir(parents=True)
        # We don't need to create the module file because the resolver only cares about the path.

        # Set project_root to the temp_dir
        project_root = str(temp_dir)

        result = parse_imports(str(helpers_file), project_root)

        # Expect: from_imports contains the resolved module base (src.module)
        # Because we are going up two levels from helpers.py:
        #   helpers.py is in src/utils, so level=2 goes up to src, then we add subpackage -> src.subpackage
        #   Then we import 'module' from subpackage, so the resolved module is src.subpackage.module?
        # Wait, let's think:
        #   File: /project/src/utils/helpers.py
        #   Import: from ..subpackage import module
        #   We go up two levels from the file's directory:
        #       file_dir = /project/src/utils
        #       level=2 -> go up 1 (because level-1) -> /project/src
        #   Then we add the module 'subpackage' -> /project/src/subpackage
        #   Then we convert to module notation: src.subpackage
        #   Then we add the imported name 'module'?
        #   But note: the existing resolver only returns the package path, not the imported name.
        #   However, our new code for bare relative imports does not apply here because module is not None.
        #   So we are using the old branch: resolve_relative_import(file_path, module, level, project_root)
        #   This returns the directory of the module as a module path (without the imported name).
        #   The analyzer's convention is to record the module base (the package) in from_imports.
        #   So we expect 'src.subpackage' (the package containing the module) and not the imported name.
        #   This matches the existing behavior for non-bare relative imports.

        assert len(result['from_imports']) == 1
        assert 'src.subpackage' in result['from_imports']
        assert len(result['imports']) == 0

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        os.remove(file_path)
