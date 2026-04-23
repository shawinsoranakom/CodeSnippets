async def lifespan(app: FastAPI) -> AsyncGenerator[dict[str, bool], None]:
        state.app_startup = True
        yield {"app": True}
        state.app_shutdown = True