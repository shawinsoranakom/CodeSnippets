def test_legitimate_root_path_still_appears():
    app = FastAPI()

    @app.get("/")
    def read_root():  # pragma: no cover
        return {"ok": True}

    client = TestClient(app, root_path="/api/v1")
    response = client.get("/openapi.json")
    data = response.json()
    servers = [s.get("url") for s in data.get("servers", [])]
    assert "/api/v1" in servers