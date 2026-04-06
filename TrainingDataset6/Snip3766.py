def test_response_with_depends_default():
    """Response type hint should work with Response = Depends(...)."""
    app = FastAPI()

    def modify_response(response: Response) -> Response:
        response.headers["X-Custom"] = "modified"
        return response

    @app.get("/")
    def endpoint(response: Response = Depends(modify_response)):
        return {"status": "ok"}

    client = TestClient(app)
    resp = client.get("/")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert resp.headers.get("X-Custom") == "modified"