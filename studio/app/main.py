from __future__ import annotations

import json
import os
import sqlite3
import hashlib
import mimetypes
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote

from .model_router import normalized_selection, public_registry, test_connection
from .github_sync import public_github_status, repository_from_payload, verify_webhook_signature
from .preview import resolve_preview_file


APP_VERSION = "0.1.0"
PROJECTS_ROOT = Path(os.environ.get("PROJECTS_ROOT", "/projects"))
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", "/data/studio.db"))
GITHUB_ALLOWED_REPOSITORY = os.environ.get("GITHUB_ALLOWED_REPOSITORY", "Good-Comic/CodexGame")
GITHUB_WORK_BRANCH = os.environ.get("GITHUB_WORK_BRANCH", "codex/project-forge-foundation")
MAX_REQUEST_BYTES = 16_384

HTML = """<!doctype html>
<html lang="zh-Hant">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Project Forge AI</title>
    <style>
      :root { color-scheme: dark; font-family: system-ui, sans-serif; }
      body { margin: 0; background: #0b1020; color: #e8edf7; }
      header { padding: 1rem 1.5rem; border-bottom: 1px solid #2b3852; }
      main { min-height: calc(100vh - 9rem); display: grid; grid-template-columns: 16rem 1fr 18rem; }
      section, aside { padding: 1rem; border-right: 1px solid #2b3852; }
      .preview { display: grid; place-items: center; color: #9fb0c8; }
      .status { border-top: 1px solid #2b3852; padding: .8rem 1.5rem; color: #71e6a2; }
      .muted { color: #9fb0c8; } button, input { padding: .55rem; margin: .25rem 0; }
      a { color: #72b7ff; } ul { padding-left: 1.2rem; }
    </style>
  </head>
  <body>
    <header><strong>Project Forge AI</strong> <span class="muted">Private Studio foundation</span></header>
    <main>
      <aside>
        <h2>Projects</h2>
        <ul id="projects"><li class="muted">Loading…</li></ul>
        <form id="import-form">
          <label>Workspace directory<br><input id="project-path" required placeholder="my-game"></label><br>
          <button type="submit">Import local</button>
        </form>
        <p id="import-result" class="muted"></p>
        <h2>Agent Tasks</h2>
        <form id="task-form">
          <input id="task-title" required placeholder="Task title"><br>
          <textarea id="task-requirement" required maxlength="6000" placeholder="Requirement"></textarea><br>
          <button type="submit">Queue ticket</button>
        </form>
        <ul id="tasks"><li class="muted">No tasks.</li></ul>
      </aside>
      <section class="preview">
        <div>
          <h2>Game preview</h2>
          <button id="reload-preview">Reload</button>
          <p id="preview-empty" class="muted">No imported project has an index.html.</p>
          <iframe id="preview-frame" title="Game preview" sandbox="allow-scripts"
            style="width: min(60vw, 900px); height: 60vh; border: 1px solid #557"></iframe>
        </div>
      </section>
      <aside>
        <h2>Agent</h2>
        <label>Provider<br><select id="provider"></select></label><br>
        <label>Model ID<br><input id="model" placeholder="model-name"></label><br>
        <label>Fallback<br><input id="fallback" placeholder="optional"></label><br>
        <label>Mode<br><select id="mode"><option>plan</option><option>edit</option><option>test</option></select></label><br>
        <button id="save-model">Save selection</button> <button id="test-provider">Test connection</button>
        <p id="model-result" class="muted"></p>
        <a href="http://127.0.0.1:8000/canvas">Open optional Agent Canvas</a>
        <h2>GitHub Sync</h2>
        <pre id="github-status" class="muted">Loading…</pre>
      </aside>
    </main>
    <footer class="status" id="status">Checking API…</footer>
    <script>
      const projects = document.querySelector('#projects');
      const status = document.querySelector('#status');
      const result = document.querySelector('#import-result');
      const modelResult = document.querySelector('#model-result');
      const providerSelect = document.querySelector('#provider');
      const modelInput = document.querySelector('#model');
      const fallbackInput = document.querySelector('#fallback');
      const modeSelect = document.querySelector('#mode');
      const githubStatus = document.querySelector('#github-status');
      const previewFrame = document.querySelector('#preview-frame');
      const previewEmpty = document.querySelector('#preview-empty');
      const taskList = document.querySelector('#tasks');
      let activeProjectId = null;
      async function refresh() {
        const health = await fetch('/health').then(r => r.json());
        const data = await fetch('/api/projects').then(r => r.json());
        activeProjectId = data.projects.length ? data.projects[0].id : null;
        status.textContent = `API ${health.status} · ${data.projects.length} project(s)`;
        projects.replaceChildren();
        if (!data.projects.length) {
          const item = document.createElement('li');
          item.textContent = 'No project imported. Create a directory under workspace/ and import its name.';
          item.className = 'muted'; projects.append(item);
        }
        for (const project of data.projects) {
          const item = document.createElement('li'); item.textContent = project.name; projects.append(item);
        }
      }
      document.querySelector('#import-form').addEventListener('submit', async event => {
        event.preventDefault(); result.textContent = 'Importing…';
        const response = await fetch('/api/projects/import-local', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({path: document.querySelector('#project-path').value})
        });
        const body = await response.json();
        result.textContent = response.ok ? `Imported ${body.project.name}` : body.detail;
        await refresh();
      });
      async function loadTasks() {
        const data = await fetch('/api/tasks').then(r => r.json());
        taskList.replaceChildren();
        for (const task of data.tasks) {
          const item = document.createElement('li');
          item.textContent = `#${task.id} ${task.title} · ${task.state} · ${task.branch}`;
          taskList.append(item);
        }
        if (!data.tasks.length) {
          const item = document.createElement('li'); item.textContent = 'No tasks.';
          item.className = 'muted'; taskList.append(item);
        }
      }
      document.querySelector('#task-form').addEventListener('submit', async event => {
        event.preventDefault();
        if (!activeProjectId) { status.textContent = 'Import a project before creating a task.'; return; }
        const response = await fetch('/api/tasks', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({project_id: activeProjectId,
            title: document.querySelector('#task-title').value,
            requirement: document.querySelector('#task-requirement').value,
            spec_ref: 'studio-input', max_retries: 2})
        });
        const body = await response.json();
        status.textContent = response.ok ? `Queued ${body.task.branch}` : body.detail;
        await loadTasks();
      });
      async function loadProviders() {
        const data = await fetch('/api/providers').then(r => r.json());
        const select = providerSelect; select.replaceChildren();
        for (const provider of data.providers) {
          const option = document.createElement('option'); option.value = provider.id;
          option.textContent = `${provider.label} · tools ${provider.tool_calls ?? 'Unknown'}`;
          select.append(option);
        }
      }
      async function loadGitHubStatus() {
        const data = await fetch('/api/github/status').then(r => r.json());
        githubStatus.textContent = `${data.repository}\n${data.branch}\n${data.sync_state}`;
      }
      async function loadPreview() {
        const data = await fetch('/api/previews').then(r => r.json());
        previewEmpty.textContent = data.previews.length
          ? `Previewing ${data.previews[0].name}`
          : 'No imported project has an index.html.';
        previewFrame.src = data.previews.length ? data.previews[0].url : 'about:blank';
      }
      document.querySelector('#reload-preview').addEventListener('click', () => {
        if (previewFrame.src !== 'about:blank') previewFrame.contentWindow.location.reload();
      });
      document.querySelector('#save-model').addEventListener('click', async () => {
        const response = await fetch('/api/models/select', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({provider: providerSelect.value, model: modelInput.value,
            fallback_model: fallbackInput.value || null, mode: modeSelect.value, task_summary: ''})
        });
        const body = await response.json();
        modelResult.textContent = response.ok
          ? `Selected ${body.selection.model} (${body.selection.effective_mode}) ${body.selection.warning ?? ''}`
          : body.detail;
      });
      document.querySelector('#test-provider').addEventListener('click', async () => {
        const response = await fetch('/api/providers/test', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({provider: providerSelect.value})
        });
        const body = await response.json();
        modelResult.textContent = response.ok ? JSON.stringify(body.result) : body.detail;
      });
      loadProviders().catch(error => { modelResult.textContent = `Provider registry unavailable: ${error}`; });
      loadGitHubStatus().catch(error => { githubStatus.textContent = `GitHub status unavailable: ${error}`; });
      loadPreview().catch(error => { previewEmpty.textContent = `Preview unavailable: ${error}`; });
      loadTasks().catch(error => { status.textContent = `Tasks unavailable: ${error}`; });
      refresh().catch(error => { status.textContent = `API unavailable: ${error}`; });
    </script>
  </body>
</html>"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    relative_path TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    project_id INTEGER,
                    detail TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS webhook_deliveries (
                    delivery_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    project_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    requirement TEXT NOT NULL,
                    spec_ref TEXT NOT NULL,
                    branch TEXT,
                    state TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL,
                    token_budget INTEGER NOT NULL,
                    time_budget_minutes INTEGER NOT NULL,
                    summary TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );
                CREATE TABLE IF NOT EXISTS project_locks (
                    project_id INTEGER PRIMARY KEY,
                    task_id INTEGER NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );
                """
            )

    def list_projects(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, name, relative_path, created_at FROM projects ORDER BY name"
            ).fetchall()
        return [dict(row) for row in rows]

    def project_by_name(self, name: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id, name, relative_path, created_at FROM projects WHERE name = ?", (name,)
            ).fetchone()
        return dict(row) if row else None

    def import_project(self, name: str, relative_path: str) -> dict[str, Any]:
        created_at = utc_now()
        with self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO projects(name, relative_path, created_at) VALUES (?, ?, ?)",
                (name, relative_path, created_at),
            )
            row = connection.execute(
                "SELECT id, name, relative_path, created_at FROM projects WHERE relative_path = ?",
                (relative_path,),
            ).fetchone()
            assert row is not None
            connection.execute(
                "INSERT INTO events(event_type, project_id, detail, created_at) VALUES (?, ?, ?, ?)",
                ("project.imported", row["id"], json.dumps({"relative_path": relative_path}), created_at),
            )
        return dict(row)

    def list_events(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, event_type, project_id, detail, created_at FROM events ORDER BY id DESC LIMIT 100"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_model_selection(self) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key = 'model_selection'").fetchone()
        return json.loads(row["value"]) if row else None

    def save_model_selection(self, selection: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO settings(key, value, updated_at) VALUES ('model_selection', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (json.dumps(selection), utc_now()),
            )
        return selection

    def record_webhook(
        self, delivery_id: str, event_type: str, repository: str, payload_hash: str
    ) -> bool:
        try:
            with self.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO webhook_deliveries(
                        delivery_id, event_type, repository, payload_hash, state, created_at
                    ) VALUES (?, ?, ?, ?, 'pending', ?)
                    """,
                    (delivery_id, event_type, repository, payload_hash, utc_now()),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    def last_webhook(self) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT delivery_id, event_type, repository, state, created_at
                FROM webhook_deliveries ORDER BY created_at DESC LIMIT 1
                """
            ).fetchone()
        return dict(row) if row else None

    def create_task(self, body: dict[str, object]) -> dict[str, Any]:
        project_id = body.get("project_id")
        title = body.get("title")
        requirement = body.get("requirement")
        spec_ref = body.get("spec_ref", "")
        max_retries = body.get("max_retries", 2)
        token_budget = body.get("token_budget", 20_000)
        time_budget = body.get("time_budget_minutes", 30)
        if not isinstance(project_id, int):
            raise ValueError("project_id must be an integer")
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            raise ValueError("title must be between 1 and 200 characters")
        if not isinstance(requirement, str) or not requirement.strip() or len(requirement) > 6_000:
            raise ValueError("requirement must be between 1 and 6000 characters")
        if not isinstance(spec_ref, str) or len(spec_ref) > 500:
            raise ValueError("spec_ref must be at most 500 characters")
        if not isinstance(max_retries, int) or not 0 <= max_retries <= 5:
            raise ValueError("max_retries must be between 0 and 5")
        if not isinstance(token_budget, int) or not 1 <= token_budget <= 1_000_000:
            raise ValueError("token_budget is outside the allowed range")
        if not isinstance(time_budget, int) or not 1 <= time_budget <= 1_440:
            raise ValueError("time_budget_minutes is outside the allowed range")
        now = utc_now()
        with self.connect() as connection:
            if not connection.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone():
                raise ValueError("project does not exist")
            cursor = connection.execute(
                """
                INSERT INTO tasks(
                    project_id, title, requirement, spec_ref, state, max_retries,
                    token_budget, time_budget_minutes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'queued', ?, ?, ?, ?, ?)
                """,
                (
                    project_id, title.strip(), requirement.strip(), spec_ref,
                    max_retries, token_budget, time_budget, now, now,
                ),
            )
            task_id = cursor.lastrowid
            connection.execute(
                "UPDATE tasks SET branch = ? WHERE id = ?", (f"codex/task-{task_id}", task_id)
            )
        task = self.task_by_id(int(task_id))
        assert task is not None
        return task

    def task_by_id(self, task_id: int) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row) if row else None

    def list_tasks(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

    def start_task(self, task_id: int) -> dict[str, Any]:
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            task = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not task or task["state"] != "queued":
                raise ValueError("task is not queued")
            try:
                connection.execute(
                    "INSERT INTO project_locks(project_id, task_id, created_at) VALUES (?, ?, ?)",
                    (task["project_id"], task_id, utc_now()),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError("project workspace is locked by another task") from error
            connection.execute(
                "UPDATE tasks SET state = 'running', updated_at = ? WHERE id = ?",
                (utc_now(), task_id),
            )
        result = self.task_by_id(task_id)
        assert result is not None
        return result

    def record_task_result(self, task_id: int, passed: bool, summary: str) -> dict[str, Any]:
        if len(summary) > 6_000:
            raise ValueError("summary must be at most 6000 characters")
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            task = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not task or task["state"] != "running":
                raise ValueError("task is not running")
            retry_count = task["retry_count"]
            if passed:
                state = "qa_passed"
            else:
                retry_count += 1
                state = "retry_pending" if retry_count <= task["max_retries"] else "stopped"
            connection.execute(
                """
                UPDATE tasks SET state = ?, retry_count = ?, summary = ?, updated_at = ?
                WHERE id = ?
                """,
                (state, retry_count, summary, utc_now(), task_id),
            )
            connection.execute("DELETE FROM project_locks WHERE task_id = ?", (task_id,))
        result = self.task_by_id(task_id)
        assert result is not None
        return result

    def retry_task(self, task_id: int) -> dict[str, Any]:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE tasks SET state = 'queued', updated_at = ?
                WHERE id = ? AND state = 'retry_pending'
                """,
                (utc_now(), task_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("task is not retryable")
        result = self.task_by_id(task_id)
        assert result is not None
        return result


def resolve_project(projects_root: Path, requested_path: object) -> Path:
    if not isinstance(requested_path, str) or not requested_path.strip():
        raise ValueError("path must be a non-empty workspace-relative directory")
    relative = Path(requested_path)
    if relative.is_absolute():
        raise ValueError("absolute paths are not allowed")
    root = projects_root.resolve(strict=True)
    candidate = (root / relative).resolve(strict=True)
    if not candidate.is_relative_to(root) or candidate == root:
        raise ValueError("project must remain inside the workspace root")
    if not candidate.is_dir():
        raise ValueError("project path must be a directory")
    return candidate


def import_local(database: Database, projects_root: Path, requested_path: object) -> dict[str, Any]:
    project_path = resolve_project(projects_root, requested_path)
    root = projects_root.resolve(strict=True)
    relative_path = project_path.relative_to(root).as_posix()
    return database.import_project(project_path.name, relative_path)


class Handler(BaseHTTPRequestHandler):
    server_version = "ProjectForge/0.1"
    sys_version = ""
    database: Database
    projects_root: Path
    github_allowed_repository: str
    github_work_branch: str
    github_webhook_secret: bytes
    github_app_configured: bool

    def do_GET(self) -> None:
        routes: dict[str, Callable[[], object]] = {
            "/health": lambda: {"status": "ok", "service": "project-forge-studio", "version": APP_VERSION},
            "/api/health": lambda: {"status": "ok", "service": "project-forge-studio", "version": APP_VERSION},
            "/api/projects": lambda: {"projects": self.database.list_projects()},
            "/api/capabilities": lambda: {
                "features": {
                    "studio_foundation": "validated",
                    "model_router": "implemented; providers not connected in this environment",
                    "github": "signed webhook core implemented; GitHub App not configured",
                    "game_preview": "sandbox adapter validated with demo; Riftwatch source unavailable",
                    "automation": "task governance implemented; Agent executor not connected",
                    "hardening": "loopback development controls only; not public-deployment ready",
                }
            },
            "/api/changes": lambda: {"changes": self.database.list_events()},
            "/api/providers": lambda: {"providers": public_registry()},
            "/api/models/current": lambda: {"selection": self.database.get_model_selection()},
            "/api/github/status": lambda: public_github_status(
                self.github_allowed_repository,
                self.github_work_branch,
                self.github_app_configured,
                bool(self.github_webhook_secret),
                self.database.last_webhook(),
            ),
            "/api/previews": self._preview_projects,
            "/api/tasks": lambda: {"tasks": self.database.list_tasks()},
            "/api/requirements": lambda: {
                "requirements": [
                    {
                        "task_id": task["id"],
                        "source": task["spec_ref"],
                        "requirement": task["requirement"],
                        "branch": task["branch"],
                        "status": task["state"],
                    }
                    for task in self.database.list_tasks()
                ]
            },
            "/api/security": lambda: {
                "exposure": "loopback-only",
                "public_deployment_ready": False,
                "authentication": "required before LAN or Internet exposure",
                "permissions": {
                    "read": True,
                    "edit": False,
                    "execute": False,
                    "push": False,
                    "merge": False,
                    "deploy": False,
                },
            },
        }
        if self.path in routes:
            self._respond_json(routes[self.path]())
        elif self.path == "/":
            self._respond(HTTPStatus.OK, "text/html; charset=utf-8", HTML.encode())
        elif self.path.startswith("/preview/"):
            self._serve_preview()
        else:
            self._respond_json({"detail": "Not Found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if not self._origin_allowed():
            self._respond_json({"detail": "cross-origin request rejected"}, HTTPStatus.FORBIDDEN)
            return
        if self.path == "/api/projects/import-local":
            self._import_project()
        elif self.path == "/api/models/select":
            self._select_model()
        elif self.path == "/api/providers/test":
            self._test_provider()
        elif self.path == "/api/github/webhook":
            self._github_webhook()
        elif self.path == "/api/tasks":
            self._create_task()
        elif self.path.startswith("/api/tasks/"):
            self._task_action()
        else:
            self._respond_json({"detail": "Not Found"}, HTTPStatus.NOT_FOUND)

    def _import_project(self) -> None:
        try:
            body = self._read_json()
            project = import_local(self.database, self.projects_root, body.get("path"))
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as error:
            self._respond_json({"detail": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._respond_json({"project": project}, HTTPStatus.CREATED)

    def _select_model(self) -> None:
        try:
            selection = normalized_selection(self._read_json())
        except (json.JSONDecodeError, ValueError) as error:
            self._respond_json({"detail": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._respond_json({"selection": self.database.save_model_selection(selection)})

    def _test_provider(self) -> None:
        try:
            provider = self._read_json().get("provider")
            if not isinstance(provider, str):
                raise ValueError("provider must be a string")
            result = test_connection(provider)
        except (json.JSONDecodeError, ValueError) as error:
            self._respond_json({"detail": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._respond_json({"result": result})

    def _github_webhook(self) -> None:
        try:
            body = self._read_body()
            if not verify_webhook_signature(
                self.github_webhook_secret, body, self.headers.get("X-Hub-Signature-256")
            ):
                self._respond_json({"detail": "invalid webhook signature"}, HTTPStatus.UNAUTHORIZED)
                return
            payload = json.loads(body)
            repository = repository_from_payload(payload)
            if repository != self.github_allowed_repository:
                self._respond_json({"detail": "repository is not authorized"}, HTTPStatus.FORBIDDEN)
                return
            delivery_id = self.headers.get("X-GitHub-Delivery")
            event_type = self.headers.get("X-GitHub-Event")
            if not delivery_id or not event_type:
                raise ValueError("GitHub delivery and event headers are required")
            created = self.database.record_webhook(
                delivery_id, event_type, repository, hashlib.sha256(body).hexdigest()
            )
        except (json.JSONDecodeError, ValueError) as error:
            self._respond_json({"detail": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._respond_json(
            {"accepted": True, "duplicate": not created, "state": "pending"}, HTTPStatus.ACCEPTED
        )

    def _create_task(self) -> None:
        try:
            task = self.database.create_task(self._read_json())
        except (json.JSONDecodeError, ValueError) as error:
            self._respond_json({"detail": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._respond_json({"task": task}, HTTPStatus.CREATED)

    def _task_action(self) -> None:
        parts = self.path.split("/")
        if len(parts) != 5:
            self._respond_json({"detail": "Not Found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            task_id = int(parts[3])
            action = parts[4]
            if action == "start":
                task = self.database.start_task(task_id)
            elif action == "result":
                body = self._read_json()
                passed = body.get("passed")
                summary = body.get("summary", "")
                if not isinstance(passed, bool) or not isinstance(summary, str):
                    raise ValueError("passed must be boolean and summary must be a string")
                task = self.database.record_task_result(task_id, passed, summary)
            elif action == "retry":
                task = self.database.retry_task(task_id)
            else:
                self._respond_json({"detail": "Not Found"}, HTTPStatus.NOT_FOUND)
                return
        except (json.JSONDecodeError, ValueError) as error:
            self._respond_json({"detail": str(error)}, HTTPStatus.CONFLICT)
            return
        self._respond_json({"task": task})

    def _preview_projects(self) -> dict[str, object]:
        previews = []
        for project in self.database.list_projects():
            try:
                resolve_preview_file(self.projects_root, project["relative_path"], "index.html")
            except (OSError, ValueError):
                continue
            previews.append({"name": project["name"], "url": f"/preview/{project['name']}/"})
        return {"previews": previews}

    def _serve_preview(self) -> None:
        parts = self.path.removeprefix("/preview/").split("/", 1)
        project_name = unquote(parts[0])
        requested_file = unquote(parts[1]) if len(parts) > 1 and parts[1] else "index.html"
        project = self.database.project_by_name(project_name)
        if not project:
            self._respond_json({"detail": "preview project is not registered"}, HTTPStatus.NOT_FOUND)
            return
        try:
            file_path = resolve_preview_file(
                self.projects_root, project["relative_path"], requested_file
            )
        except (OSError, ValueError) as error:
            self._respond_json({"detail": str(error)}, HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self._respond(
            HTTPStatus.OK,
            content_type,
            file_path.read_bytes(),
            headers={
                "Content-Security-Policy": "sandbox allow-scripts",
                "Cache-Control": "no-store",
                "Access-Control-Allow-Origin": "*",
            },
        )

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_REQUEST_BYTES:
            raise ValueError("request body size is invalid")
        return self.rfile.read(length)

    def _origin_allowed(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True
        host = self.headers.get("Host", "")
        return origin in {f"http://{host}", f"https://{host}"}

    def _read_json(self) -> dict[str, object]:
        body = json.loads(self._read_body())
        if not isinstance(body, dict):
            raise ValueError("request body must be a JSON object")
        return body

    def log_message(self, message_format: str, *args: object) -> None:
        print(f"{self.address_string()} - {message_format % args}", flush=True)

    def _respond_json(self, body: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        self._respond(status, "application/json", json.dumps(body).encode())

    def _respond(
        self,
        status: HTTPStatus,
        content_type: str,
        body: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if "Content-Security-Policy" not in (headers or {}):
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
                "frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'",
            )
        if "Cache-Control" not in (headers or {}):
            self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)


def serve() -> None:
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    Handler.projects_root = PROJECTS_ROOT
    Handler.database = Database(DATABASE_PATH)
    Handler.github_allowed_repository = GITHUB_ALLOWED_REPOSITORY
    Handler.github_work_branch = GITHUB_WORK_BRANCH
    Handler.github_webhook_secret = os.environ.get("PF_GITHUB_WEBHOOK_SECRET", "").encode()
    Handler.github_app_configured = bool(
        os.environ.get("PF_GITHUB_APP_ID") and os.environ.get("PF_GITHUB_APP_PRIVATE_KEY")
    )
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    print("Project Forge Studio listening on http://0.0.0.0:8080", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    serve()
