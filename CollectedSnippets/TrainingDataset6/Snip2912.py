def test_configured_servers_not_mutated():
    configured_servers = [{"url": "https://prod.example.com"}]
    app = FastAPI(servers=configured_servers)

    @app.get("/")
    def read_root():  # pragma: no cover
        return {"ok": True}

    # Request with a rogue root_path
    attacker_client = TestClient(app, root_path="/evil")
    attacker_client.get("/openapi.json")

    # The original servers list must be untouched
    assert configured_servers == [{"url": "https://prod.example.com"}]