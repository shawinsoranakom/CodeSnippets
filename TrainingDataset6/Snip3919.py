def test_merged_no_return_lifespans_return_none() -> None:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield

    @asynccontextmanager
    async def router_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield

    router = APIRouter(lifespan=router_lifespan)
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)

    with TestClient(app) as client:
        assert not client.app_state