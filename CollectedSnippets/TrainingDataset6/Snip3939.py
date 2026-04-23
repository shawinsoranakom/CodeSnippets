async def router_lifespan(
        app: FastAPI,
    ) -> AsyncGenerator[dict[str, str | bool], None]:
        yield {
            "router_specific": True,
            "overridden": "router",  # should override parent
        }