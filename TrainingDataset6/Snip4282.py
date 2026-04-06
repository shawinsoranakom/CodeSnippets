def test_keepalive_ping_sync(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(fastapi.routing, "_PING_INTERVAL", 0.05)
    with TestClient(keepalive_app) as c:
        response = c.get("/slow-sync")
    assert response.status_code == 200
    text = response.text
    assert ": ping\n" in text
    data_lines = [line for line in text.split("\n") if line.startswith("data: ")]
    assert len(data_lines) == 2