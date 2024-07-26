import pytest
import psycopg2
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.main import app

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@db/test_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

@pytest.fixture(scope="module")
def test_db():
    try:
        con = psycopg2.connect(dbname='postgres', user='postgres', password='postgres', host='db')
        con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        cur.execute("DROP DATABASE IF EXISTS test_db")
        cur.execute("CREATE DATABASE test_db")
        cur.close()
        con.close()
    except psycopg2.OperationalError as e:
        pytest.fail(f"Could not connect to the PostgreSQL server: {e}")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

    Base.metadata.drop_all(bind=engine)
    con = psycopg2.connect(dbname='postgres', user='postgres', password='postgres', host='db')
    con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    cur.execute("REVOKE CONNECT ON DATABASE test_db FROM public;")
    cur.execute("SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'test_db' AND pid <> pg_backend_pid();")
    cur.execute("DROP DATABASE IF EXISTS test_db")
    cur.close()
    con.close()

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_create_document(client, test_db):
    response = client.post("/documents/", json={"rubrics": ["test"], "text": "Test document"})
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Test document"
    assert "id" in data

def test_get_document(client, test_db):
    # First, create a document
    create_response = client.post("/documents/", json={"rubrics": ["test"], "text": "Test document"})
    document_id = create_response.json()["id"]

    response = client.get(f"/documents/{document_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document_id
    assert data["text"] == "Test document"

def test_search_documents(client, test_db):
    # Create a document to search for
    create_response = client.post("/documents/", json={"rubrics": ["test"], "text": "Searchable document"})
    assert create_response.status_code == 200

    # Search for the document
    response = client.get("/search", params={"query": "Searchable"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(doc["text"] == "Searchable document" for doc in data)


def test_delete_document(client, test_db):
    # First, create a document
    create_response = client.post("/documents/", json={"rubrics": ["test"], "text": "Deletable document"})
    document_id = create_response.json()["id"]

    # Then, delete the document
    delete_response = client.delete(f"/documents/{document_id}")
    assert delete_response.status_code == 200

    # Finally, try to get the deleted document
    get_response = client.get(f"/documents/{document_id}")
    assert get_response.status_code == 404
