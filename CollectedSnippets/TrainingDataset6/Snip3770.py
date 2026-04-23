def test_request_with_depends_annotated():
    """Request type hint should work in dependency chain."""
    app = FastAPI()

    def extract_request_info(request: Request) -> dict:
        return {
            "path": request.url.path,
            "user_agent": request.headers.get("user-agent", "unknown"),
        }

    @app.get("/")
    def endpoint(
        info: Annotated[dict, Depends(extract_request_info)],
    ):
        return info

    client = TestClient(app)
    resp = client.get("/", headers={"user-agent": "test-agent"})

    assert resp.status_code == 200
    assert resp.json() == {"path": "/", "user_agent": "test-agent"}