import sqlite3
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def db(tmp_path):
    """Return a fresh SQLite connection in a temp directory."""
    db_path = str(tmp_path / 'names.db')
    conn = sqlite3.connect(db_path)
    yield conn, db_path
    conn.close()


def run_migration(db_path):
    """Execute the same SQL as migrate.py against the given DB path."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS names (id INTEGER PRIMARY KEY, name TEXT)')
    conn.commit()
    conn.close()


# ── Schema ───────────────────────────────────────────────────────────────────

def test_migration_creates_names_table(db):
    _, db_path = db
    run_migration(db_path)
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='names'"
    ).fetchone()
    conn.close()
    assert row is not None


def test_migration_creates_id_column(db):
    _, db_path = db
    run_migration(db_path)
    conn = sqlite3.connect(db_path)
    columns = [col[1] for col in conn.execute('PRAGMA table_info(names)').fetchall()]
    conn.close()
    assert 'id' in columns


def test_migration_creates_name_column(db):
    _, db_path = db
    run_migration(db_path)
    conn = sqlite3.connect(db_path)
    columns = [col[1] for col in conn.execute('PRAGMA table_info(names)').fetchall()]
    conn.close()
    assert 'name' in columns


def test_id_is_primary_key(db):
    _, db_path = db
    run_migration(db_path)
    conn = sqlite3.connect(db_path)
    pk_cols = [
        col[1] for col in conn.execute('PRAGMA table_info(names)').fetchall()
        if col[5] == 1  # pk flag
    ]
    conn.close()
    assert 'id' in pk_cols


def test_id_autoincrements(db):
    _, db_path = db
    run_migration(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute('INSERT INTO names (name) VALUES (?)', ('Alice',))
    conn.execute('INSERT INTO names (name) VALUES (?)', ('Bob',))
    conn.commit()
    rows = conn.execute('SELECT id FROM names ORDER BY id').fetchall()
    conn.close()
    assert rows[0][0] == 1
    assert rows[1][0] == 2


# ── Idempotency ──────────────────────────────────────────────────────────────

def test_migration_is_idempotent(db):
    """Running migration twice must not raise an error."""
    _, db_path = db
    run_migration(db_path)
    run_migration(db_path)  # should not raise


def test_migration_does_not_wipe_existing_data(db):
    """Re-running migration must not delete rows already in the table."""
    _, db_path = db
    run_migration(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute('INSERT INTO names (name) VALUES (?)', ('Alice',))
    conn.commit()
    conn.close()

    run_migration(db_path)  # second run

    conn = sqlite3.connect(db_path)
    count = conn.execute('SELECT COUNT(*) FROM names').fetchone()[0]
    conn.close()
    assert count == 1
