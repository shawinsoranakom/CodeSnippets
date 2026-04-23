def test_response_without_depends():
    """Regular Response injection should still work."""
    app = FastAPI()

    @app.get("/")
    def endpoint(response: Response):
        response.headers["X-Direct"] = "set"
        return {"status": "ok"}

    client = TestClient(app)
    resp = client.get("/")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert resp.headers.get("X-Direct") == "set"