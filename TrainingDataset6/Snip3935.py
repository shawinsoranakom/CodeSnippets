async def router_lifespan(app: FastAPI) -> AsyncGenerator[dict[str, bool], None]:
        state.router_startup = True
        yield {"router": True}
        state.router_shutdown = True