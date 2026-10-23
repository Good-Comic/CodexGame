# Private deployment checklist

- [ ] Use a private host with sufficient disk and Docker `overlay2`; validate Agent Canvas there.
- [ ] Configure OAuth/OIDC, HTTPS, secure cookies, CSRF protection, and rate limiting.
- [ ] Store model and GitHub credentials in an encrypted server-side secret store.
- [ ] Register a least-privilege GitHub App for selected repositories only.
- [ ] Expose webhook ingress only through authenticated HTTPS and retain delivery audit records.
- [ ] Configure per-job CPU, memory, disk, time, and egress limits.
- [ ] Schedule SQLite backups, Git refs backups, workspace snapshots, and perform restore drills.
- [ ] Run unit, integration, preview, browser, secret, dependency, and image vulnerability scans.
- [ ] Verify logs and front-end assets contain no API keys or private repository content.
- [ ] Obtain explicit approval before push, PR merge, public deployment, or publishing a game.
