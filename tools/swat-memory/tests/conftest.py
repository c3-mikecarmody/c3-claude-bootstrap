"""Shared fixtures: tmp DB + deterministic embedder stub (no fastembed download)."""
from __future__ import annotations

import hashlib

import numpy as np
import pytest

from swat_memory import config, db, embeddings


def _stub_encode(texts: list[str]) -> np.ndarray:
    """Deterministic pseudo-embedding derived from SHA-256 of the text.
    Not semantically meaningful; identical inputs produce identical vectors.
    For similarity tests we use explicit overrides in individual cases."""
    out = np.zeros((len(texts), config.EMBED_DIM), dtype=np.float32)
    for i, t in enumerate(texts):
        h = hashlib.sha256(t.encode("utf-8")).digest()
        # Tile hash into the vector; normalize lightly so cosine behaves.
        raw = np.frombuffer((h * (config.EMBED_DIM // len(h) + 1))[: config.EMBED_DIM * 4], dtype=np.uint8).astype(np.float32)
        raw = raw[: config.EMBED_DIM]
        out[i] = (raw - raw.mean()) / (raw.std() + 1e-6)
    return out


@pytest.fixture(autouse=True)
def _stub_embedder():
    embeddings.set_encoder_override(_stub_encode)
    yield
    embeddings.set_encoder_override(None)


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    db_path = tmp_path / "memory.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(config, "LOG_DIR", tmp_path)
    c = db.connect(db_path)
    db.bootstrap(c)
    yield c
    c.close()


@pytest.fixture()
def vec_encoder(monkeypatch):
    """Factory: caller provides {text: vector}. Falls back to stub for unmapped strings."""
    def _make(mapping: dict[str, list[float]]):
        def _enc(texts):
            out = []
            for t in texts:
                if t in mapping:
                    out.append(np.asarray(mapping[t], dtype=np.float32))
                else:
                    out.append(_stub_encode([t])[0])
            return np.stack(out)
        embeddings.set_encoder_override(_enc)
    return _make
