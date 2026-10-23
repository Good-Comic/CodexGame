# Project Forge AI threat model

## Trust boundaries

- Repository files, README content, issues, pull requests, game assets, and model output are
  untrusted data. They are never treated as Studio control instructions.
- The Studio API accepts only structured operations. It has no endpoint that executes arbitrary
  shell commands or fetches a caller-provided URL.
- Projects must resolve beneath `/projects`; symlinks and `..` paths escaping that root are rejected.
- Provider endpoints and credentials are server configuration. Credentials are not returned by GET
  endpoints, written to SQLite, placed in browser storage, or included in logs.
- GitHub webhook payloads require HMAC-SHA256, an allowed repository, and a unique delivery ID.

## Current controls

- Host ports bind to `127.0.0.1` only.
- The Studio container drops Linux capabilities except `DAC_OVERRIDE`, which is needed to traverse
  the explicitly mounted cloud bind directories. It enables `no-new-privileges`, uses a read-only
  root filesystem, and does not mount the Docker socket.
- Request bodies are capped at 16 KiB. Task/spec summaries are capped at 6,000 characters.
- Preview paths are constrained to registered projects and served with a sandbox CSP; the iframe
  uses `sandbox="allow-scripts"` without same-origin privileges.
- High-risk actions (push, merge, deploy, secret configuration) are not exposed as browser actions.

## Known gaps before LAN or Internet access

- Add OAuth/OIDC authentication, secure server-side sessions, CSRF tokens, HTTPS termination,
  rate limits, and an audited authorization policy.
- Use an encrypted secrets service and short-lived GitHub App installation tokens.
- Run Agent jobs in separate resource- and network-constrained sandboxes.
- Add a durable worker queue, dead-letter replay, telemetry retention policy, backup scheduling,
  and a tested disaster-recovery runbook.
- Complete dependency/SBOM scanning and external penetration testing.

Until those gaps are closed, Project Forge AI is a loopback-only development system, not a public
deployment.
