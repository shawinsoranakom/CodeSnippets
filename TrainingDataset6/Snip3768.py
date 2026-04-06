def test_response_dependency_chain():
    """Response dependency should work in a chain of dependencies."""
    app = FastAPI()

    def first_modifier(response: Response) -> Response:
        response.headers["X-First"] = "1"
        return response

    def second_modifier(
        response: Annotated[Response, Depends(first_modifier)],
    ) -> Response:
        response.headers["X-Second"] = "2"
        return response

    @app.get("/")
    def endpoint(response: Annotated[Response, Depends(second_modifier)]):
        return {"status": "ok"}

    client = TestClient(app)
    resp = client.get("/")

    assert resp.status_code == 200
    assert resp.headers.get("X-First") == "1"
    assert resp.headers.get("X-Second") == "2"