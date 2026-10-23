from __future__ import annotations

import json
import hashlib
import hmac
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import Database, Handler, resolve_project  # noqa: E402
from app.preview import resolve_preview_file  # noqa: E402
from app.backup import backup_database  # noqa: E402


class ProjectPathTests(unittest.TestCase):
    def test_project_must_remain_inside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as root_name, tempfile.TemporaryDirectory() as outside_name:
            root = Path(root_name)
            (root / "valid").mkdir()
            self.assertEqual(resolve_project(root, "valid"), (root / "valid").resolve())
            (root / "escape").symlink_to(outside_name, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "inside the workspace"):
                resolve_project(root, "escape")
            with self.assertRaisesRegex(ValueError, "absolute paths"):
                resolve_project(root, outside_name)

    def test_preview_file_must_remain_inside_project(self) -> None:
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            project = root / "game"
            project.mkdir()
            (project / "index.html").write_text("demo")
            (root / "outside.html").write_text("outside")
            self.assertEqual(resolve_preview_file(root, "game", "index.html"), project / "index.html")
            with self.assertRaisesRegex(ValueError, "outside the project"):
                resolve_preview_file(root, "game", "../outside.html")

    def test_database_backup_can_be_restored(self) -> None:
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            database = Database(root / "studio.db")
            database.import_project("demo", "demo")
            backup = backup_database(database.path, root / "backups" / "studio.db")
            restored = Database(backup)
            self.assertEqual(restored.list_projects()[0]["name"], "demo")


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.projects_root = root / "projects"
        self.projects_root.mkdir()
        (self.projects_root / "demo-game").mkdir()
        (self.projects_root / "demo-game" / "index.html").write_text("<h1>Demo game</h1>")
        Handler.projects_root = self.projects_root
        Handler.database = Database(root / "studio.db")
        Handler.github_allowed_repository = "Good-Comic/CodexGame"
        Handler.github_work_branch = "codex/test"
        Handler.github_webhook_secret = b"unit-test-secret"
        Handler.github_app_configured = False
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def request(
        self,
        path: str,
        body: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, object]]:
        data = json.dumps(body).encode() if body is not None else None
        request_headers = {"Content-Type": "application/json"} if data else {}
        request_headers.update(headers or {})
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers=request_headers,
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_project_import_and_event_history(self) -> None:
        status, imported = self.request("/api/projects/import-local", {"path": "demo-game"})
        self.assertEqual(status, 201)
        self.assertEqual(imported["project"]["name"], "demo-game")
        _, projects = self.request("/api/projects")
        self.assertEqual(len(projects["projects"]), 1)
        _, changes = self.request("/api/changes")
        self.assertEqual(changes["changes"][0]["event_type"], "project.imported")

    def test_path_traversal_is_rejected(self) -> None:
        status, body = self.request("/api/projects/import-local", {"path": "../outside"})
        self.assertEqual(status, 400)
        self.assertIn("detail", body)

    def test_model_selection_downgrades_unknown_tool_capability(self) -> None:
        status, body = self.request(
            "/api/models/select",
            {"provider": "ollama", "model": "local-test", "mode": "edit", "task_summary": "small task"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["selection"]["effective_mode"], "plan")
        self.assertIn("downgraded", body["selection"]["warning"])
        _, current = self.request("/api/models/current")
        self.assertEqual(current["selection"]["model"], "local-test")

    def test_public_provider_registry_contains_no_secret_fields(self) -> None:
        _, body = self.request("/api/providers")
        serialized = json.dumps(body)
        self.assertNotIn("key_environment", serialized)
        self.assertNotIn("API_KEY", serialized)

    def test_webhook_signature_repository_allowlist_and_deduplication(self) -> None:
        payload = {"repository": {"full_name": "Good-Comic/CodexGame"}}
        raw = json.dumps(payload).encode()
        signature = "sha256=" + hmac.new(b"unit-test-secret", raw, hashlib.sha256).hexdigest()
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Delivery": "delivery-1",
            "X-GitHub-Event": "push",
        }
        first_status, first = self.request("/api/github/webhook", payload, headers)
        second_status, second = self.request("/api/github/webhook", payload, headers)
        self.assertEqual(first_status, 202)
        self.assertFalse(first["duplicate"])
        self.assertEqual(second_status, 202)
        self.assertTrue(second["duplicate"])

    def test_webhook_rejects_invalid_signature(self) -> None:
        status, _ = self.request(
            "/api/github/webhook",
            {"repository": {"full_name": "Good-Comic/CodexGame"}},
            {"X-Hub-Signature-256": "sha256=bad"},
        )
        self.assertEqual(status, 401)

    def test_registered_project_preview_is_sandboxed(self) -> None:
        self.request("/api/projects/import-local", {"path": "demo-game"})
        with urllib.request.urlopen(self.base_url + "/preview/demo-game/") as response:
            body = response.read().decode()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["Content-Security-Policy"], "sandbox allow-scripts")
            self.assertIn("Demo game", body)

    def test_task_workspace_lock_and_retry_limit(self) -> None:
        _, imported = self.request("/api/projects/import-local", {"path": "demo-game"})
        project_id = imported["project"]["id"]
        task_body = {
            "project_id": project_id,
            "title": "Test task",
            "requirement": "Keep this context small",
            "spec_ref": "requirements/demo.md#test",
            "max_retries": 1,
        }
        _, first = self.request("/api/tasks", task_body)
        _, second = self.request("/api/tasks", {**task_body, "title": "Second task"})
        first_id = first["task"]["id"]
        second_id = second["task"]["id"]
        start_status, _ = self.request(f"/api/tasks/{first_id}/start", {})
        locked_status, locked = self.request(f"/api/tasks/{second_id}/start", {})
        self.assertEqual(start_status, 200)
        self.assertEqual(locked_status, 409)
        self.assertIn("locked", locked["detail"])
        _, failed_once = self.request(
            f"/api/tasks/{first_id}/result", {"passed": False, "summary": "compile failed"}
        )
        self.assertEqual(failed_once["task"]["state"], "retry_pending")
        self.request(f"/api/tasks/{first_id}/retry", {})
        self.request(f"/api/tasks/{first_id}/start", {})
        _, stopped = self.request(
            f"/api/tasks/{first_id}/result", {"passed": False, "summary": "failed again"}
        )
        self.assertEqual(stopped["task"]["state"], "stopped")
        self.assertEqual(stopped["task"]["retry_count"], 2)
        unlocked_status, _ = self.request(f"/api/tasks/{second_id}/start", {})
        self.assertEqual(unlocked_status, 200)


if __name__ == "__main__":
    unittest.main()
