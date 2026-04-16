"""fastembed wrapper with lazy load + optional pre-warm. Float32 BLOB helpers."""
from __future__ import annotations

import threading
from typing import Iterable

import numpy as np

from . import config

_model_lock = threading.Lock()
_model = None
_override = None  # tests can inject a callable(list[str]) -> np.ndarray


def set_encoder_override(fn):
    """Test hook: replace the encoder with a deterministic callable."""
    global _override
    _override = fn


def _load():
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is None:
            # Imported lazily — fastembed pulls in heavy deps (onnxruntime).
            from fastembed import TextEmbedding
            _model = TextEmbedding(model_name=config.EMBED_MODEL)
    return _model


def prewarm() -> None:
    """Start model load on a background thread. Safe to call repeatedly."""
    if _override is not None or _model is not None:
        return
    threading.Thread(target=_load, name="swat-memory-embed-prewarm", daemon=True).start()


def encode(texts: list[str]) -> np.ndarray:
    """Return a float32 array of shape (len(texts), EMBED_DIM)."""
    if not texts:
        return np.zeros((0, config.EMBED_DIM), dtype=np.float32)
    if _override is not None:
        arr = np.asarray(_override(texts), dtype=np.float32)
        if arr.shape != (len(texts), config.EMBED_DIM):
            raise ValueError(f"override encoder returned {arr.shape}, expected {(len(texts), config.EMBED_DIM)}")
        return arr
    model = _load()
    vecs = list(model.embed(texts))
    return np.asarray(vecs, dtype=np.float32)


def encode_one(text: str) -> np.ndarray:
    return encode([text])[0]


def to_blob(vec: np.ndarray) -> bytes:
    return np.asarray(vec, dtype=np.float32).tobytes()


def from_blob(blob: bytes | None) -> np.ndarray | None:
    if blob is None:
        return None
    return np.frombuffer(blob, dtype=np.float32)


def cosine_matrix(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Cosine similarity of query (D,) against rows of matrix (N, D)."""
    if matrix.size == 0:
        return np.zeros((0,), dtype=np.float32)
    qn = query / (np.linalg.norm(query) + 1e-12)
    mn = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12)
    return (mn @ qn).astype(np.float32)


def truncate_for_embed(text: str) -> str:
    return text[: config.CONTENT_EMBED_MAX_CHARS]


def batch_rows_to_matrix(rows: Iterable) -> tuple[list, np.ndarray]:
    """Decode rows with an `embedding` BLOB column. Returns (rows_with_embed, matrix)."""
    kept = []
    vecs = []
    for r in rows:
        v = from_blob(r["embedding"])
        if v is None or v.size == 0:
            continue
        kept.append(r)
        vecs.append(v)
    if not vecs:
        return [], np.zeros((0, config.EMBED_DIM), dtype=np.float32)
    return kept, np.stack(vecs)
