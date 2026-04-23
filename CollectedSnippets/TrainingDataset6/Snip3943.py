async def router_lifespan(app: FastAPI) -> AsyncGenerator[dict[str, bool], None]:
        yield {"router": True}