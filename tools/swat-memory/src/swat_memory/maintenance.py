"""Nightly maintenance CLI: decay, prune, dedupe. File-locked to avoid races."""
from __future__ import annotations

import fcntl
import logging
import sys
from pathlib import Path

from . import config, db, episodes

log = logging.getLogger("swat-memory.maintenance")


def run() -> dict:
    config.ensure_dirs()
    lock_path = Path(str(config.DB_PATH) + ".maint.lock")
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log.warning("maintenance already running; exiting")
        return {"skipped": True}

    try:
        with db.session() as conn:
            conn.execute("BEGIN IMMEDIATE")
            decayed = episodes.decay(conn)
            pruned = episodes.prune(conn)
            deduped = episodes.dedupe(conn)
            db.set_meta(conn, "last_maintenance", _now())
            conn.execute("COMMIT")
        return {"decayed": decayed, "pruned": pruned, "deduped": deduped}
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    result = run()
    log.info("maintenance result: %s", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
