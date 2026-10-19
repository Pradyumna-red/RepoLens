"""Pydantic models for RepoLens analysis responses."""

from typing import Dict, List
from pydantic import BaseModel, Field


class FileAnalysis(BaseModel):
    """Import information for one Python file."""

    path: str
    name: str
    imports: List[str] = Field(default_factory=list)
    from_imports: List[str] = Field(default_factory=list)
    import_count: int = 0


class DependencyGraph(BaseModel):
    """Project-local dependencies and reverse dependencies."""

    graph: Dict[str, List[str]] = Field(default_factory=dict)
    imported_by: Dict[str, List[str]] = Field(default_factory=dict)
    import_counts: Dict[str, int] = Field(default_factory=dict)
    unresolved_imports: Dict[str, List[str]] = Field(default_factory=dict)


class AnalysisResponse(BaseModel):
    """Backward-compatible analysis response with graph data."""

    message: str
    project_name: str
    total_files: int
    total_imports: int
    files: List[FileAnalysis] = Field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict)
    imported_by: Dict[str, List[str]] = Field(default_factory=dict)
    import_counts: Dict[str, int] = Field(default_factory=dict)
    unresolved_imports: Dict[str, List[str]] = Field(default_factory=dict)
