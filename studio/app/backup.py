from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def backup_database(source: Path, destination: Path) -> Path:
    if not source.is_file():
        raise FileNotFoundError(f"database does not exist: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as source_connection, sqlite3.connect(destination) as target_connection:
        source_connection.backup(target_connection)
        row = target_connection.execute("PRAGMA integrity_check").fetchone()
        if not row or row[0] != "ok":
            raise RuntimeError("backup integrity check failed")
    return destination


def main() -> None:
    source = Path(os.environ.get("DATABASE_PATH", "/data/studio.db"))
    backup_root = Path(os.environ.get("BACKUP_DIRECTORY", "/data/backups"))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_root / f"studio-{timestamp}.db"
    print(backup_database(source, destination))


if __name__ == "__main__":
    main()
