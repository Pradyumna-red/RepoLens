"""
AST-based Python import analyzer.
Extracts import statements from Python source files safely without execution.
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Optional, Sequence, Union, Any


def parse_imports(file_path: str, project_root: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Parse a Python file and extract all import statements using AST.

    Args:
        file_path: Path to the Python file to analyze
        project_root: Root directory of the project (for resolving relative imports)

    Returns:
        Dictionary with two keys:
        - 'imports': List of imported module names
        - 'from_imports': List of modules imported via 'from x import y'

    Example:
        For a file containing:
            import os
            from pathlib import Path

        Returns:
            {
                'imports': ['os'],
                'from_imports': ['pathlib']
            }
    """
    imports = []
    from_imports = []

    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        # Parse the source code into an AST
        tree = ast.parse(source_code, filename=file_path)

        # Walk through all nodes in the AST
        for node in ast.walk(tree):
            # Handle standard imports: import os, import sys
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)

            # Handle from imports: from pathlib import Path
            elif isinstance(node, ast.ImportFrom):
                module = node.module

                # Handle relative imports (from . import x or from .. import y)
                if node.level > 0:
                    if project_root:
                        # When module is None, we have bare relative imports like "from . import x"
                        # In this case, we need to resolve each imported name as a relative target
                        if module is None:
                            # For "from . import sibling", resolve each alias as the relative target
                            for alias in node.names:
                                resolved = resolve_relative_import(
                                    file_path,
                                    alias.name,
                                    node.level,
                                    project_root
                                )
                                if resolved:
                                    from_imports.append(resolved)
                        else:
                            # For "from ..subpackage import module", resolve the module normally
                            resolved = resolve_relative_import(
                                file_path,
                                module,
                                node.level,
                                project_root
                            )
                            if resolved:
                                from_imports.append(resolved)
                    else:
                        # If no project root, store as relative
                        prefix = '.' * node.level
                        if module:
                            module_name = f"{prefix}{module}"
                            from_imports.append(module_name)
                        else:
                            # Bare relative import without project root
                            from_imports.extend(
                                f"{prefix}{alias.name}" for alias in node.names
                            )
                else:
                    # Absolute import
                    if module:
                        from_imports.append(module)

    except SyntaxError:
        # File has syntax errors - skip it
        pass
    except Exception as e:
        # Other errors - log but don't crash
        print(f"Warning: Failed to parse {file_path}: {e}")

    return {
        'imports': imports,
        'from_imports': from_imports
    }


def resolve_relative_import(
    file_path: str,
    module: Optional[str],
    level: int,
    project_root: str
) -> Optional[str]:
    """
    Resolve a relative import to an absolute module path.

    Args:
        file_path: Path to the file containing the import
        module: The module name (can be None for 'from . import x')
        level: Number of dots (1 for '.', 2 for '..', etc.)
        project_root: Root directory of the project

    Returns:
        Resolved module path, or None if resolution fails

    Example:
        File: /project/src/utils/helpers.py
        Import: from .. import config (level=2, module='config')
        Result: src.config
    """
    try:
        # Get the directory containing the file
        file_dir = Path(file_path).parent

        # Go up 'level - 1' directories (level includes current package)
        # level=1 means current package, level=2 means parent, etc.
        target_dir = file_dir
        for _ in range(level - 1):
            target_dir = target_dir.parent

        # Get relative path from project root
        try:
            rel_path = target_dir.relative_to(project_root)
        except ValueError:
            # Path is outside project root
            return None

        # Convert path to module notation
        module_parts = list(rel_path.parts) if rel_path.parts else []

        # Add the module name if specified
        if module:
            module_parts.append(module)

        # Join with dots
        if module_parts:
            return '.'.join(module_parts)
        else:
            return module if module else None

    except Exception:
        return None


def build_dependency_graph(
    python_files: Sequence[Union[str, Dict[str, str]]],
    project_root: str
) -> Dict[str, Any]:
    """
    Build project-local dependency and reverse-dependency mappings.

    External or unresolved imports are reported separately and never become
    project graph edges. Source files are parsed with ``parse_imports`` only;
    uploaded code is never imported or executed.

    Args:
        python_files: File paths or file metadata dictionaries returned by
            ``file_handler.find_python_files``.
        project_root: Root directory containing the project files.

    Returns:
        A dictionary containing ``graph``, ``imported_by``, ``import_counts``,
        and ``unresolved_imports`` mappings keyed by project-relative paths.
    """
    root = Path(project_root).resolve()
    file_paths = []
    for item in python_files:
        path_value = item['path'] if isinstance(item, dict) else item
        path = Path(path_value)
        if not path.is_absolute():
            path = root / path
        file_paths.append(path.resolve())

    # Use forward-slash relative paths as stable graph node identifiers.
    project_files = [
        (path, str(path.relative_to(root)).replace('\\', '/'))
        for path in file_paths
        if path.is_relative_to(root) and path.suffix == '.py'
    ]
    project_files.sort(key=lambda item: item[1])
    nodes = [node for _, node in project_files]
    node_set = set(nodes)

    module_to_node = {}
    for node in nodes:
        module_path = node[:-3] if node.endswith('.py') else node
        if module_path.endswith('/__init__'):
            module_path = module_path[:-9].rstrip('/')
        module_name = module_path.replace('/', '.')
        module_to_node[module_name] = node

    def resolve_import(import_name: str) -> Optional[str]:
        """Resolve an import name to a known project node, if possible."""
        normalized = import_name.replace('\\', '/').lstrip('./')
        if normalized.endswith('.py'):
            normalized = normalized[:-3]

        for candidate in (normalized, normalized.replace('.', '/')):
            direct = f"{candidate}.py"
            package = f"{candidate}/__init__.py"
            if direct in node_set:
                return direct
            if package in node_set:
                return package
        return module_to_node.get(import_name)

    graph = {node: [] for node in nodes}
    unresolved = {node: [] for node in nodes}

    for source_path, source_node in project_files:
        imports = parse_imports(str(source_path), str(root))

        imported_names = imports['imports'] + imports['from_imports']
        for imported_name in imported_names:
            target_node = resolve_import(imported_name)
            if target_node:
                if target_node not in graph[source_node]:
                    graph[source_node].append(target_node)
            else:
                if imported_name not in unresolved[source_node]:
                    unresolved[source_node].append(imported_name)

    for node in nodes:
        graph[node].sort()
        unresolved[node].sort()

    imported_by = {node: [] for node in nodes}
    for source_node, targets in graph.items():
        for target_node in targets:
            imported_by[target_node].append(source_node)
    for node in nodes:
        imported_by[node].sort()

    return {
        'graph': graph,
        'imported_by': imported_by,
        'import_counts': {node: len(graph[node]) for node in nodes},
        'unresolved_imports': unresolved,
    }


def detect_circular_imports(graph: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """Return each directed cycle in an adjacency-list dependency graph once.

    The graph is treated as data only.  Each cycle is represented as a closed
    chain whose first node is repeated at the end for display.
    """
    nodes = sorted(set(graph) | {neighbor for targets in graph.values() for neighbor in targets})
    cycles = {}

    def canonical_cycle(path: List[str], start_index: int) -> tuple[str, ...]:
        cycle = path[start_index:]
        rotations = [
            tuple(cycle[index:] + cycle[:index])
            for index in range(len(cycle))
        ]
        return min(rotations)

    def dfs(start: str, current: str, path: List[str], in_path: set[str]) -> None:
        for neighbor in sorted(graph.get(current, [])):
            if neighbor == start:
                key = canonical_cycle(path, 0)
                cycles[key] = list(key) + [key[0]]
            elif neighbor not in in_path and neighbor in graph:
                in_path.add(neighbor)
                path.append(neighbor)
                dfs(start, neighbor, path, in_path)
                path.pop()
                in_path.remove(neighbor)

    for start in nodes:
        dfs(start, start, [start], {start})

    return [
        {
            'cycle': cycle,
            'description': ' → '.join(cycle),
        }
        for cycle in (cycles[key] for key in sorted(cycles))
    ]


def get_all_imports(file_path: str, project_root: Optional[str] = None) -> List[str]:
    """
    Get a flat list of all imports from a file.

    Args:
        file_path: Path to the Python file
        project_root: Root directory of the project

    Returns:
        List of all imported module names (both import and from import)
    """
    result = parse_imports(file_path, project_root)
    return result['imports'] + result['from_imports']


def analyze_file(file_path: str, project_root: Optional[str] = None) -> Dict:
    """
    Analyze a single Python file and return import information.

    Args:
        file_path: Path to the Python file
        project_root: Root directory of the project

    Returns:
        Dictionary with file analysis results:
        {
            'file': relative_path,
            'imports': list of imports,
            'from_imports': list of from imports,
            'all_imports': combined list
        }
    """
    result = parse_imports(file_path, project_root)

    # Get relative path if project_root is provided
    if project_root:
        try:
            rel_path = str(Path(file_path).relative_to(project_root))
        except ValueError:
            rel_path = file_path
    else:
        rel_path = file_path

    return {
        'file': rel_path.replace('\\', '/'),  # Normalize path separators
        'imports': result['imports'],
        'from_imports': result['from_imports'],
        'all_imports': result['imports'] + result['from_imports']
    }
