from __future__ import annotations

from pathlib import Path


def resolve_preview_file(projects_root: Path, relative_project: str, requested_file: str) -> Path:
    root = projects_root.resolve(strict=True)
    project = (root / relative_project).resolve(strict=True)
    if not project.is_relative_to(root) or project == root:
        raise ValueError("preview project is outside the workspace")
    candidate = (project / (requested_file or "index.html")).resolve(strict=True)
    if not candidate.is_relative_to(project) or not candidate.is_file():
        raise ValueError("preview file is outside the project or missing")
    return candidate
