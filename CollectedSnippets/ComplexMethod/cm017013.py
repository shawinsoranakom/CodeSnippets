def test_router_nested_lifespan_state(state: State) -> None:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[dict[str, bool], None]:
        state.app_startup = True
        yield {"app": True}
        state.app_shutdown = True

    @asynccontextmanager
    async def router_lifespan(app: FastAPI) -> AsyncGenerator[dict[str, bool], None]:
        state.router_startup = True
        yield {"router": True}
        state.router_shutdown = True

    @asynccontextmanager
    async def subrouter_lifespan(app: FastAPI) -> AsyncGenerator[dict[str, bool], None]:
        state.sub_router_startup = True
        yield {"sub_router": True}
        state.sub_router_shutdown = True

    sub_router = APIRouter(lifespan=subrouter_lifespan)

    router = APIRouter(lifespan=router_lifespan)
    router.include_router(sub_router)

    app = FastAPI(lifespan=lifespan)
    app.include_router(router)

    @app.get("/")
    def main(request: Request) -> dict[str, str]:
        assert request.state.app
        assert request.state.router
        assert request.state.sub_router
        return {"message": "Hello World"}

    assert state.app_startup is False
    assert state.router_startup is False
    assert state.sub_router_startup is False
    assert state.app_shutdown is False
    assert state.router_shutdown is False
    assert state.sub_router_shutdown is False

    with TestClient(app) as client:
        assert state.app_startup is True
        assert state.router_startup is True
        assert state.sub_router_startup is True
        assert state.app_shutdown is False
        assert state.router_shutdown is False
        assert state.sub_router_shutdown is False
        response = client.get("/")
        assert response.status_code == 200, response.text
        assert response.json() == {"message": "Hello World"}

    assert state.app_startup is True
    assert state.router_startup is True
    assert state.sub_router_startup is True
    assert state.app_shutdown is True
    assert state.router_shutdown is True
    assert state.sub_router_shutdown is True