def test_router_async_shutdown_handler(state: State) -> None:
    """Test that async on_shutdown event handlers are called correctly, for coverage."""
    app = FastAPI()

    @app.get("/")
    def main() -> dict[str, str]:
        return {"message": "Hello World"}

    @app.on_event("shutdown")
    async def app_shutdown() -> None:
        state.app_shutdown = True

    assert state.app_shutdown is False
    with TestClient(app) as client:
        assert state.app_shutdown is False
        response = client.get("/")
        assert response.status_code == 200, response.text
    assert state.app_shutdown is True