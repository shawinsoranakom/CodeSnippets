def test_router_nested_lifespan_state_overriding_by_parent() -> None:
    @asynccontextmanager
    async def lifespan(
        app: FastAPI,
    ) -> AsyncGenerator[dict[str, str | bool], None]:
        yield {
            "app_specific": True,
            "overridden": "app",
        }

    @asynccontextmanager
    async def router_lifespan(
        app: FastAPI,
    ) -> AsyncGenerator[dict[str, str | bool], None]:
        yield {
            "router_specific": True,
            "overridden": "router",  # should override parent
        }

    router = APIRouter(lifespan=router_lifespan)
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)

    with TestClient(app) as client:
        assert client.app_state == {
            "app_specific": True,
            "router_specific": True,
            "overridden": "app",
        }