# Project Forge AI progress

Validated in the Debian cloud development container on 2026-10-23. These results describe the
cloud development instance, not a permanent private-host deployment.

## Task 01 — Foundation

- Implemented the four-region Studio UI, SQLite project/event storage, controlled local import,
  `/health`, `/api/projects`, `/api/projects/import-local`, and `/api/changes`.
- Workspace traversal and escaping symlinks are rejected. `ProjectForgeAI` was imported through the
  real API and returned by the project list.
- `docker compose up --build --detach --wait studio-api`: passed; the container is `healthy` and
  binds only to `127.0.0.1:8080`.
- OpenHands Agent Canvas remains an optional `agent` profile. Its 1.29.0 image could not be expanded
  by this cloud daemon's `vfs` storage driver (`no space left on device`), so Canvas is not marked
  as validated.

## Task 02 — Model router

- Implemented Ollama, OpenAI-compatible, and OpenHands provider registry entries; runtime model and
  fallback selection; capability visibility; task-summary limit; and safe plan-mode downgrade when
  tool-call support is unknown.
- Provider credentials are server-only and are absent from GET APIs and browser storage.
- Model selection was changed without restarting the Studio. Ollama connection testing correctly
  returned `connected: false` because no Ollama service exists here. No cloud provider credential
  was configured or charged.

## Task 03 — GitHub

- Implemented GitHub status, repository allowlisting, HMAC-SHA256 webhook validation, payload hash
  auditing, delivery idempotency, and pending-event persistence.
- The work is on `codex/project-forge-foundation`; `main` was not modified.
- GitHub App installation, public HTTPS webhook ingress, automatic PR creation, and merge remain
  unconfigured and unclaimed.

## Task 04 — Preview

- Implemented a registered-project preview adapter, sandboxed iframe, manual reload, no-store
  static assets, and path containment checks.
- Playwright smoke passed for the supplied demo: HTTP 200, four languages, Start interaction, and
  zero console/page errors.
- The ZIP did not include the Riftwatch game source. Vite HMR and the real 10-wave regression suite
  therefore remain unrun rather than being reported as successful.

## Task 05 — Automation

- Implemented traceable tickets, per-task branch names, token/time/retry budgets, 6,000-character
  context limits, requirement matrix API, project locking, QA result states, and bounded retries.
- Tests prove a second task cannot lock the same project and a deliberately failed task stops after
  the configured retry limit.
- No connected Agent executor or GitHub App exists, so queued tasks do not edit files or create PRs.

## Task 06 — Hardening

- Added security headers, same-origin POST checks, request limits, preview CSP, loopback-only
  exposure, read-only container root, dropped capabilities, `no-new-privileges`, and CPU/RAM/PID/log
  limits. The Docker socket is not mounted.
- Added a threat model, private deployment checklist, SQLite online backup, integrity verification,
  and a restore test.
- OAuth/OIDC, HTTPS, encrypted secret service, isolated Agent workers, durable queue/dead-letter
  replay, telemetry, and external security review are mandatory before LAN or Internet exposure.

## Test evidence

- `python3 -m unittest discover -s studio/tests -v`: 11 tests passed.
- `node studio/tests/preview_smoke.cjs`: passed.
- `node --check` on the served Studio JavaScript: passed.
- Compose build/start/health and service restart checks: passed for `studio-api`.
- Actual backup: `/data/backups/studio-20261023T143725Z.db`, with SQLite integrity check passed.
- Preview headers include `Content-Security-Policy: sandbox allow-scripts`.
