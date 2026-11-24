"""End-to-end tests against the real app with the mock engine (no model or GPU needed)."""
import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GGUFBOX_ENGINE", "mock")
    monkeypatch.setenv("GGUFBOX_MODELS_DIR", str(tmp_path / "models"))
    monkeypatch.setenv("GGUFBOX_DATA_DIR", str(tmp_path / "data"))
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "tiny-Q4_K_M.gguf").write_bytes(b"0" * 1024)
    from app.config import get_settings
    get_settings.cache_clear()
    from app.main import create_app
    with TestClient(create_app()) as c:
        yield c


def events(response):
    out, ev = [], None
    for line in response.text.splitlines():
        if line.startswith("event:"):
            ev = line[6:].strip()
        elif line.startswith("data:"):
            out.append((ev, json.loads(line[5:])))
    return out


def load(client):
    return client.post("/api/models/load", json={"filename": "tiny-Q4_K_M.gguf"})


def test_models_listed_and_loadable(client):
    assert client.get("/api/models").json()[0]["quant"] == "Q4_K_M"
    assert load(client).json()["loaded"] is True


def test_chat_requires_a_loaded_model(client):
    chat = client.post("/api/chats", json={}).json()
    r = client.post(f"/api/chats/{chat['id']}/messages", json={"content": "hi"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "no_model_loaded"


def test_streaming_chat_persists_and_splits_reasoning(client):
    load(client)
    chat = client.post("/api/chats", json={}).json()
    r = client.post(f"/api/chats/{chat['id']}/messages", json={"content": "hello there", "thinking": True})
    kinds = [e for e, _ in events(r)]
    assert kinds[0] == "meta" and "reasoning" in kinds and "token" in kinds and kinds[-1] == "done"
    saved = client.get(f"/api/chats/{chat['id']}").json()
    assert [m["role"] for m in saved["messages"]] == ["user", "assistant"]
    assert saved["messages"][1]["reasoning"] and saved["title"].startswith("hello")


def test_thinking_off_hides_reasoning(client):
    load(client)
    chat = client.post("/api/chats", json={}).json()
    r = client.post(f"/api/chats/{chat['id']}/messages", json={"content": "hello", "thinking": False})
    assert "reasoning" not in [e for e, _ in events(r)]


def test_export_and_openai_compat(client):
    load(client)
    chat = client.post("/api/chats", json={}).json()
    client.post(f"/api/chats/{chat['id']}/messages", json={"content": "ping", "stream": False})
    assert "ping" in client.get(f"/api/chats/{chat['id']}/export?format=md").text
    r = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.json()["choices"][0]["message"]["content"].startswith("Mock reply")


def test_virtual_api_with_schema_returns_json(client):
    load(client)
    body = {"slug": "echoer", "name": "Echoer", "input_template": "Say: {{input}}",
            "output_schema": {"type": "object"}}
    assert client.post("/api/virtual-apis", json=body).status_code == 201
    r = client.post("/api/v/echoer", json={"input": "x"})
    assert isinstance(r.json()["output"], dict)


def test_path_traversal_is_rejected(client):
    assert client.post("/api/models/load", json={"filename": "../secret.gguf"}).status_code == 404
