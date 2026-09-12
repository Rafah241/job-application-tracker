import sys
import os
import sqlite3
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_jobs.db"

    app.config["TESTING"] = True

    def test_connection():
        return sqlite3.connect(str(test_db))

    monkeypatch.setattr(app_module, "get_db_connection", lambda: create_test_connection(test_db))

    conn = sqlite3.connect(str(test_db))
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            date_applied TEXT,
            status TEXT,
            job_link TEXT,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()

    with app.test_client() as client:
        yield client


def create_test_connection(test_db):
    conn = sqlite3.connect(str(test_db))
    conn.row_factory = sqlite3.Row
    return conn


def test_home_page(client):
    response = client.get("/")

    assert response.status_code == 200


def test_invalid_application():
    from app import validate_application

    errors = validate_application(
        "",
        "",
        "2026-99-99",
        "InvalidStatus",
        "hello"
    )

    assert len(errors) == 5


def test_add_application(client):
    response = client.post(
        "/add",
        data={
            "company": "Test Company",
            "role": "Software Engineer",
            "date_applied": "2026-09-12",
            "status": "Applied",
            "job_link": "https://example.com/job",
            "notes": "Test application"
        }
    )

    assert response.status_code == 302

def test_delete_application(client):
    client.post(
        "/add",
        data={
            "company": "Delete Test",
            "role": "Software Engineer",
            "date_applied": "2026-09-12",
            "status": "Applied",
            "job_link": "https://example.com/job",
            "notes": "Delete test"
        }
    )

    response = client.post("/delete/1")

    assert response.status_code == 302