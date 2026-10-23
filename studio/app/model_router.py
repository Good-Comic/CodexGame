from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Provider:
    id: str
    label: str
    endpoint_environment: str | None
    default_endpoint: str | None
    key_environment: str | None
    tool_calls: bool | None
    vision: bool | None
    json_support: bool | None
    context_window: int | None
    cost_notice: str


PROVIDERS = {
    "ollama": Provider(
        id="ollama",
        label="Local Ollama",
        endpoint_environment="OLLAMA_BASE_URL",
        default_endpoint="http://host.docker.internal:11434/v1",
        key_environment=None,
        tool_calls=None,
        vision=None,
        json_support=None,
        context_window=None,
        cost_notice="Runs on your own Ollama host; hardware costs are local.",
    ),
    "openai-compatible": Provider(
        id="openai-compatible",
        label="OpenAI-compatible API",
        endpoint_environment="OPENAI_COMPATIBLE_BASE_URL",
        default_endpoint=None,
        key_environment="PF_OPENAI_COMPATIBLE_API_KEY",
        tool_calls=None,
        vision=None,
        json_support=None,
        context_window=None,
        cost_notice="Cloud provider usage may incur charges; verify before running tasks.",
    ),
    "openhands": Provider(
        id="openhands",
        label="OpenHands Agent Canvas",
        endpoint_environment=None,
        default_endpoint="http://127.0.0.1:8000/canvas",
        key_environment=None,
        tool_calls=True,
        vision=None,
        json_support=None,
        context_window=None,
        cost_notice="Cost depends on the provider configured in OpenHands.",
    ),
}


def public_registry() -> list[dict[str, Any]]:
    result = []
    for provider in PROVIDERS.values():
        item = asdict(provider)
        item.pop("key_environment")
        endpoint = configured_endpoint(provider)
        item["configured"] = bool(endpoint)
        item.pop("endpoint_environment")
        item.pop("default_endpoint")
        result.append(item)
    return result


def configured_endpoint(provider: Provider) -> str | None:
    if provider.endpoint_environment:
        return os.environ.get(provider.endpoint_environment) or provider.default_endpoint
    return provider.default_endpoint


def normalized_selection(body: dict[str, object]) -> dict[str, Any]:
    provider_id = body.get("provider")
    model = body.get("model")
    fallback_model = body.get("fallback_model")
    requested_mode = body.get("mode", "plan")
    task_summary = body.get("task_summary", "")
    if provider_id not in PROVIDERS:
        raise ValueError("unknown provider")
    if not isinstance(model, str) or not model.strip() or len(model) > 200:
        raise ValueError("model must be a non-empty string")
    if fallback_model is not None and (not isinstance(fallback_model, str) or len(fallback_model) > 200):
        raise ValueError("fallback_model must be a string or null")
    if requested_mode not in {"plan", "edit", "test"}:
        raise ValueError("mode must be plan, edit, or test")
    if not isinstance(task_summary, str) or len(task_summary) > 6_000:
        raise ValueError("task_summary must be at most 6000 characters")
    provider = PROVIDERS[str(provider_id)]
    effective_mode = requested_mode
    warning = None
    if requested_mode != "plan" and provider.tool_calls is not True:
        effective_mode = "plan"
        warning = "Tool-call capability is unknown; downgraded to plan mode."
    return {
        "provider": provider.id,
        "model": model.strip(),
        "fallback_model": fallback_model.strip() if isinstance(fallback_model, str) else None,
        "requested_mode": requested_mode,
        "effective_mode": effective_mode,
        "task_summary": task_summary,
        "warning": warning,
    }


def test_connection(provider_id: str, timeout: float = 3.0) -> dict[str, Any]:
    provider = PROVIDERS.get(provider_id)
    if provider is None:
        raise ValueError("unknown provider")
    if provider.id == "openhands":
        return {"provider": provider.id, "connected": False, "reason": "Use the Agent Canvas UI link."}
    endpoint = configured_endpoint(provider)
    if not endpoint:
        return {"provider": provider.id, "connected": False, "reason": "Endpoint is not configured."}
    request = urllib.request.Request(endpoint.rstrip("/") + "/models")
    if provider.key_environment:
        key = os.environ.get(provider.key_environment)
        if not key:
            return {"provider": provider.id, "connected": False, "reason": "Server credential is not configured."}
        request.add_header("Authorization", "Bearer " + key)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        return {"provider": provider.id, "connected": False, "reason": type(error).__name__}
    models = payload.get("data", []) if isinstance(payload, dict) else []
    return {"provider": provider.id, "connected": True, "model_count": len(models)}
