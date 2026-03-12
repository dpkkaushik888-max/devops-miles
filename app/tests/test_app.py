import sqlite3
import sys
import os
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import app as flask_app


@pytest.fixture
def client(tmp_path):
    """Test client with an isolated in-memory DB, schema pre-created."""
    db_path = str(tmp_path / 'test_names.db')

    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE names (id INTEGER PRIMARY KEY, name TEXT)')
    conn.commit()
    conn.close()

    def mock_get_db():
        return sqlite3.connect(db_path)

    flask_app.app.config['TESTING'] = True
    with patch.object(flask_app, 'get_db', mock_get_db):
        with flask_app.app.test_client() as c:
            yield c, db_path


# ── GET / ────────────────────────────────────────────────────────────────────

def test_get_homepage_returns_200(client):
    c, _ = client
    response = c.get('/')
    assert response.status_code == 200


def test_get_homepage_contains_form(client):
    c, _ = client
    response = c.get('/')
    body = response.data.decode()
    assert '<form' in body
    assert 'name="name"' in body
    assert 'type="submit"' in body


def test_get_homepage_has_no_greeting_by_default(client):
    c, _ = client
    response = c.get('/')
    assert b'Hello' not in response.data


# ── POST / ───────────────────────────────────────────────────────────────────

def test_post_returns_greeting(client):
    c, _ = client
    response = c.post('/', data={'name': 'Alice'})
    assert response.status_code == 200
    assert b'Hello, Alice!' in response.data


def test_post_persists_name_to_db(client):
    c, db_path = client
    c.post('/', data={'name': 'Bob'})
    conn = sqlite3.connect(db_path)
    row = conn.execute('SELECT name FROM names WHERE name = ?', ('Bob',)).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == 'Bob'


def test_multiple_posts_all_persist(client):
    c, db_path = client
    names = ['Alice', 'Bob', 'Charlie']
    for name in names:
        c.post('/', data={'name': name})
    conn = sqlite3.connect(db_path)
    rows = conn.execute('SELECT name FROM names ORDER BY id').fetchall()
    conn.close()
    assert [r[0] for r in rows] == names


def test_post_same_name_twice_creates_two_rows(client):
    c, db_path = client
    c.post('/', data={'name': 'Alice'})
    c.post('/', data={'name': 'Alice'})
    conn = sqlite3.connect(db_path)
    count = conn.execute('SELECT COUNT(*) FROM names WHERE name = ?', ('Alice',)).fetchone()[0]
    conn.close()
    assert count == 2


def test_get_after_post_shows_no_greeting(client):
    """A plain GET always shows a clean form regardless of prior POSTs."""
    c, _ = client
    c.post('/', data={'name': 'Alice'})
    response = c.get('/')
    assert b'Hello' not in response.data


# ── Edge cases ───────────────────────────────────────────────────────────────

def test_post_with_empty_name_returns_200(client):
    c, _ = client
    response = c.post('/', data={'name': ''})
    assert response.status_code == 200


def test_post_with_empty_name_stores_empty_string(client):
    c, db_path = client
    c.post('/', data={'name': ''})
    conn = sqlite3.connect(db_path)
    row = conn.execute('SELECT name FROM names').fetchone()
    conn.close()
    assert row is not None
    assert row[0] == ''


def test_post_with_long_name_returns_200(client):
    c, _ = client
    long_name = 'A' * 1000
    response = c.post('/', data={'name': long_name})
    assert response.status_code == 200
    assert f'Hello, {long_name}!'.encode() in response.data


def test_post_xss_name_is_escaped_in_response(client):
    """Flask's render_template_string auto-escapes {{ greeting }} — verify."""
    c, _ = client
    xss = '<script>alert(1)</script>'
    response = c.post('/', data={'name': xss})
    body = response.data.decode()
    assert '<script>' not in body
    assert '&lt;script&gt;' in body


def test_post_with_special_characters_persists_correctly(client):
    c, db_path = client
    name = "O'Brien & Co."
    c.post('/', data={'name': name})
    conn = sqlite3.connect(db_path)
    row = conn.execute('SELECT name FROM names').fetchone()
    conn.close()
    assert row[0] == name


# ── GET /healthz ─────────────────────────────────────────────────────────────

def test_healthz_returns_200(client):
    c, _ = client
    response = c.get('/healthz')
    assert response.status_code == 200


def test_healthz_returns_json(client):
    c, _ = client
    response = c.get('/healthz')
    assert response.content_type == 'application/json'


def test_healthz_status_ok_when_db_reachable(client):
    c, _ = client
    response = c.get('/healthz')
    data = response.get_json()
    assert data['status'] == 'ok'


def test_healthz_returns_error_when_db_unavailable(client):
    c, _ = client

    def broken_db():
        raise Exception('DB unreachable')

    with patch.object(flask_app, 'get_db', broken_db):
        response = c.get('/healthz')
    assert response.status_code == 500
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'detail' in data
