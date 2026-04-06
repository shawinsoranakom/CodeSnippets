def test_merged_mixed_state_lifespans() -> None:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield

    @asynccontextmanager
    async def router_lifespan(app: FastAPI) -> AsyncGenerator[dict[str, bool], None]:
        yield {"router": True}

    @asynccontextmanager
    async def sub_router_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield

    sub_router = APIRouter(lifespan=sub_router_lifespan)
    router = APIRouter(lifespan=router_lifespan)
    app = FastAPI(lifespan=lifespan)
    router.include_router(sub_router)
    app.include_router(router)

    with TestClient(app) as client:
        assert client.app_state == {"router": True}