from __future__ import annotations

import hashlib
import hmac
from typing import Any


def verify_webhook_signature(secret: bytes, body: bytes, signature: str | None) -> bool:
    if not secret or not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def repository_from_payload(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    repository = payload.get("repository")
    if not isinstance(repository, dict):
        return None
    full_name = repository.get("full_name")
    return full_name if isinstance(full_name, str) else None


def public_github_status(
    allowed_repository: str,
    branch: str,
    app_configured: bool,
    webhook_configured: bool,
    last_delivery: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "repository": allowed_repository,
        "branch": branch,
        "github_app_configured": app_configured,
        "webhook_configured": webhook_configured,
        "last_webhook": last_delivery,
        "pull_request": None,
        "sync_state": "local-only" if not app_configured else "configured",
    }
