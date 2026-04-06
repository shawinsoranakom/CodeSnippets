def test_response_dependency_returns_different_response_instance():
    """Dependency that returns a different Response instance should work.

    When a dependency returns a new Response object (e.g., JSONResponse) instead
    of modifying the injected one, the returned response should be used and any
    modifications to it in the endpoint should be preserved.
    """
    app = FastAPI()

    def default_response() -> Response:
        response = JSONResponse(content={"status": "ok"})
        response.headers["X-Custom"] = "initial"
        return response

    @app.get("/")
    def endpoint(response: Annotated[Response, Depends(default_response)]):
        response.headers["X-Custom"] = "modified"
        return response

    client = TestClient(app)
    resp = client.get("/")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert resp.headers.get("X-Custom") == "modified"