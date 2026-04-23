async def subrouter_lifespan(app: FastAPI) -> AsyncGenerator[dict[str, bool], None]:
        state.sub_router_startup = True
        yield {"sub_router": True}
        state.sub_router_shutdown = True