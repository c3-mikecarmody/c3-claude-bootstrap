"""Runtime constants. Paths resolve to the user's home by default; override via env."""
from __future__ import annotations

import os
from pathlib import Path

HOME = Path.home()

DB_PATH = Path(os.environ.get("SWAT_MEMORY_DB", HOME / ".claude" / "swat-memory" / "memory.db"))
LOG_DIR = Path(os.environ.get("SWAT_MEMORY_LOG_DIR", HOME / ".claude" / "swat-memory"))

EMBED_MODEL = os.environ.get("SWAT_MEMORY_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
EMBED_DIM = 384  # bge-small-en-v1.5

DECAY_RATE = float(os.environ.get("SWAT_MEMORY_DECAY_RATE", "0.25"))
IMPORTANCE_CUTOFF = float(os.environ.get("SWAT_MEMORY_CUTOFF", "6.0"))
PRUNE_GRACE_DAYS = int(os.environ.get("SWAT_MEMORY_PRUNE_GRACE_DAYS", "14"))
DEDUPE_COSINE = float(os.environ.get("SWAT_MEMORY_DEDUPE_COSINE", "0.95"))

CONTENT_EMBED_MAX_CHARS = 2048
SCHEMA_VERSION = "2"

FACT_TYPES = {"user", "feedback", "project", "reference"}
ENTITY_TYPES = {"Person", "Project", "System", "Doc", "Unknown"}
RELATION_TYPES = {"works_on", "owns", "blocks", "references", "collaborates_with"}


def ensure_dirs() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
