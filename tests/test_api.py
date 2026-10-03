import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "AutoAssist AI"
    assert "endpoints" in data


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["embedding_dimension"] == 384


def test_rag_search_endpoint():
    payload = {
        "query": "What can cause an engine to overheat?",
        "top_k": 3
    }
    response = client.post("/api/rag/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert "results" in data
    assert len(data["results"]) > 0
    assert "latency_ms" in data
    assert "safety_disclaimer" in data

    first = data["results"][0]
    assert "content" in first
    assert "similarity" in first
    assert first["similarity"] > 0.4
    assert first["document_title"] is not None


def test_rag_search_validation_error():
    payload = {"query": ""}  # Query must be at least 2 chars
    response = client.post("/api/rag/search", json=payload)
    assert response.status_code == 422
