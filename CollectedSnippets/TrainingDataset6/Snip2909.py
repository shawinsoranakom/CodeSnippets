def test_root_path_does_not_persist_across_requests():
    app = FastAPI()

    @app.get("/")
    def read_root():  # pragma: no cover
        return {"ok": True}

    # Attacker request with a spoofed root_path
    attacker_client = TestClient(app, root_path="/evil-api")
    response1 = attacker_client.get("/openapi.json")
    data1 = response1.json()
    assert any(s.get("url") == "/evil-api" for s in data1.get("servers", []))

    # Subsequent legitimate request with no root_path
    clean_client = TestClient(app)
    response2 = clean_client.get("/openapi.json")
    data2 = response2.json()
    servers = [s.get("url") for s in data2.get("servers", [])]
    assert "/evil-api" not in servers