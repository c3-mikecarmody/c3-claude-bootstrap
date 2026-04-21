PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS episodes (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  summary     TEXT    NOT NULL,
  importance  REAL    NOT NULL DEFAULT 5.0,
  tags        TEXT    NOT NULL DEFAULT '[]',
  created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
  last_seen   TEXT    NOT NULL DEFAULT (datetime('now')),
  last_decay  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_episodes_importance ON episodes(importance);
CREATE INDEX IF NOT EXISTS idx_episodes_created    ON episodes(created_at);

CREATE TABLE IF NOT EXISTS facts (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  subject      TEXT    NOT NULL,
  content      TEXT    NOT NULL,
  type         TEXT    NOT NULL,
  domain       TEXT,
  confidence   REAL    NOT NULL DEFAULT 0.8,
  content_hash TEXT    NOT NULL,
  source_path  TEXT,
  created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
  updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
  UNIQUE(subject, type)
);
CREATE INDEX IF NOT EXISTS idx_facts_type   ON facts(type);
CREATE INDEX IF NOT EXISTS idx_facts_domain ON facts(domain);

CREATE TABLE IF NOT EXISTS entities (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT    NOT NULL,
  type        TEXT    NOT NULL,
  attributes  TEXT    NOT NULL DEFAULT '{}',
  created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
  UNIQUE(name, type)
);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);

CREATE TABLE IF NOT EXISTS relations (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  from_id     INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  to_id       INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  rel_type    TEXT    NOT NULL,
  attributes  TEXT    NOT NULL DEFAULT '{}',
  created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
  UNIQUE(from_id, to_id, rel_type)
);
CREATE INDEX IF NOT EXISTS idx_rel_from ON relations(from_id, rel_type);
CREATE INDEX IF NOT EXISTS idx_rel_to   ON relations(to_id,   rel_type);

CREATE TABLE IF NOT EXISTS meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS facts_vec USING vec0(
  embedding float[384] distance_metric=cosine
);

CREATE VIRTUAL TABLE IF NOT EXISTS episodes_vec USING vec0(
  embedding float[384] distance_metric=cosine
);
