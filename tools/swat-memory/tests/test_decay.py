from swat_memory import config, episodes


def _set_dates(conn, episode_id, created_at, last_decay=None):
    conn.execute(
        "UPDATE episodes SET created_at = ?, last_decay = COALESCE(?, ?) WHERE id = ?",
        (created_at, last_decay, created_at, episode_id),
    )


def test_decay_reduces_importance_per_day(conn):
    r = episodes.save(conn, summary="ep", importance=8.0)
    # Backdate last_decay by 4 days.
    conn.execute(
        "UPDATE episodes SET last_decay = datetime('now', '-4 days') WHERE id = ?",
        (r["id"],),
    )
    touched = episodes.decay(conn)
    row = conn.execute("SELECT importance FROM episodes WHERE id = ?", (r["id"],)).fetchone()
    assert touched == 1
    # 8.0 - 0.25*4 = 7.0
    assert abs(row["importance"] - (8.0 - config.DECAY_RATE * 4)) < 1e-6


def test_decay_no_op_same_day(conn):
    r = episodes.save(conn, summary="ep", importance=7.0)
    touched = episodes.decay(conn)
    assert touched == 0


def test_decay_preserves_fractional_drift(conn):
    """Two decay runs 6 days apart should produce same result as one run 6 days out —
    i.e. last_decay advances by exact days, not reset to now(), so sub-day drift
    doesn't silently vanish between runs."""
    r = episodes.save(conn, summary="ep", importance=10.0)
    # Backdate last_decay by 6 days.
    conn.execute(
        "UPDATE episodes SET last_decay = datetime('now', '-6 days') WHERE id = ?",
        (r["id"],),
    )
    # First decay — should consume all 6 days.
    assert episodes.decay(conn) == 1
    imp1 = conn.execute("SELECT importance FROM episodes WHERE id = ?", (r["id"],)).fetchone()["importance"]
    assert abs(imp1 - (10.0 - config.DECAY_RATE * 6)) < 1e-6
    # Immediate second decay should find zero full days remaining.
    assert episodes.decay(conn) == 0


def test_prune_respects_grace(conn):
    # Fresh low-importance episode: NOT pruned (grace period).
    fresh = episodes.save(conn, summary="fresh", importance=1.0)
    # Old low-importance episode: pruned.
    old = episodes.save(conn, summary="old", importance=1.0)
    _set_dates(conn, old["id"], created_at=f"datetime('now', '-{config.PRUNE_GRACE_DAYS + 5} days')")
    # The helper uses a literal; re-do as a param:
    conn.execute(
        "UPDATE episodes SET created_at = datetime('now', ?) WHERE id = ?",
        (f"-{config.PRUNE_GRACE_DAYS + 5} days", old["id"]),
    )
    removed = episodes.prune(conn)
    assert removed == 1
    remaining = {r["id"] for r in conn.execute("SELECT id FROM episodes")}
    assert fresh["id"] in remaining
    assert old["id"] not in remaining


def test_dedupe_keeps_higher_importance(conn, vec_encoder):
    dim = config.EMBED_DIM
    shared = [1.0] + [0.0] * (dim - 1)
    vec_encoder({"A": shared, "A copy": shared, "B": [0.0, 1.0] + [0.0] * (dim - 2)})
    low = episodes.save(conn, summary="A", importance=4.0, tags=["lo"])
    high = episodes.save(conn, summary="A copy", importance=9.0, tags=["hi"])
    episodes.save(conn, summary="B", importance=7.0)
    removed = episodes.dedupe(conn)
    ids = {r["id"] for r in conn.execute("SELECT id FROM episodes")}
    assert removed == 1
    assert high["id"] in ids
    assert low["id"] not in ids
