import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture
def client():
    return TestClient(main.app)


def test_query_ok(client, monkeypatch):
    captured = {}

    def fake_execute(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return [{"canal": "Globo", "total": 2}, {"canal": "Band", "total": 1}]

    monkeypatch.setattr(main, "execute_query", fake_execute)

    response = client.post("/query", json={"question": "top 5 canais da Globo nos últimos 7 dias"})

    assert response.status_code == 200
    body = response.json()
    assert body["rows"] == 2
    assert body["data"][0] == {"canal": "Globo", "total": 2}
    assert body["params"] == {"dias": 7, "canal": "globo"}
    assert body["sql"] == captured["sql"]
    assert body["sql"].endswith("LIMIT 5")


def test_query_pergunta_curta_demais(client):
    response = client.post("/query", json={"question": "a"})
    assert response.status_code == 422


def test_query_erro_de_banco_vira_500_sem_vazar_detalhes(client, monkeypatch):
    def broken_execute(sql, params):
        raise RuntimeError("senha=segredo host=10.0.0.1")

    monkeypatch.setattr(main, "execute_query", broken_execute)

    response = client.post("/query", json={"question": "canais com mais falhas"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Erro interno ao processar a consulta."}


def test_health_ok(client, monkeypatch):
    monkeypatch.setattr(main, "ping", lambda: "mysql")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "mysql"}


def test_health_sem_banco(client, monkeypatch):
    def broken_ping():
        raise RuntimeError("sem conexão")

    monkeypatch.setattr(main, "ping", broken_ping)
    response = client.get("/health")
    assert response.status_code == 503


def test_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.json()["uptime_seconds"] >= 0
