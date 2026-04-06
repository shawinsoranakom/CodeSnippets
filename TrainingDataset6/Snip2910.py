def test_multiple_different_root_paths_do_not_accumulate():
    app = FastAPI()

    @app.get("/")
    def read_root():  # pragma: no cover
        return {"ok": True}

    for prefix in ["/path-a", "/path-b", "/path-c"]:
        c = TestClient(app, root_path=prefix)
        c.get("/openapi.json")

    # A clean request should not have any of them
    clean_client = TestClient(app)
    response = clean_client.get("/openapi.json")
    data = response.json()
    servers = [s.get("url") for s in data.get("servers", [])]
    for prefix in ["/path-a", "/path-b", "/path-c"]:
        assert prefix not in servers, (
            f"root_path '{prefix}' leaked into clean request: {servers}"
        )