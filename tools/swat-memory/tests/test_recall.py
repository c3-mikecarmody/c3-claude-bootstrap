from swat_memory import config, episodes, facts, recall


def test_empty_query_returns_nothing(conn):
    assert recall.recall(conn, query="") == []


def test_recall_ranks_by_similarity(conn, vec_encoder):
    dim = config.EMBED_DIM
    apple = [1.0, 0.0] + [0.0] * (dim - 2)
    banana = [0.9, 0.1] + [0.0] * (dim - 2)
    car = [0.0, 1.0] + [0.0] * (dim - 2)
    vec_encoder({
        "apple": apple, "banana fruit": banana, "car engine": car,
        "fruit query": [0.95, 0.05] + [0.0] * (dim - 2),
    })
    facts.save(conn, subject="apple", content="apple", type="reference")
    facts.save(conn, subject="banana", content="banana fruit", type="reference")
    facts.save(conn, subject="car", content="car engine", type="reference")

    hits = recall.recall(conn, query="fruit query", k=3)
    subjects = [h["subject"] for h in hits]
    assert subjects[0] in {"apple", "banana"}
    assert "car" in subjects  # car is last
    assert subjects.index("car") == 2


def test_types_filter_excludes_episodes(conn):
    facts.save(conn, subject="fact1", content="hello world", type="project")
    episodes.save(conn, summary="some episode about hello", importance=8.0)
    hits = recall.recall(conn, query="hello", k=5, types=["project"])
    assert all(h["kind"] == "fact" for h in hits)


def test_episode_only_recall(conn):
    facts.save(conn, subject="f", content="hello", type="reference")
    episodes.save(conn, summary="episode hello")
    hits = recall.recall(conn, query="hello", k=5, types=["episode"])
    assert all(h["kind"] == "episode" for h in hits)
