def test_router_async_generator_lifespan(state: State) -> None:
    """Test that an async generator lifespan (not wrapped) works."""

    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        state.app_startup = True
        yield
        state.app_shutdown = True

    app = FastAPI(lifespan=lifespan)  # type: ignore[arg-type]

    @app.get("/")
    def main() -> dict[str, str]:
        return {"message": "Hello World"}

    assert state.app_startup is False
    assert state.app_shutdown is False
    with TestClient(app) as client:
        assert state.app_startup is True
        assert state.app_shutdown is False
        response = client.get("/")
        assert response.status_code == 200, response.text
        assert response.json() == {"message": "Hello World"}
    assert state.app_startup is True
    assert state.app_shutdown is True