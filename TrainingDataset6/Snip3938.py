async def lifespan(
        app: FastAPI,
    ) -> AsyncGenerator[dict[str, str | bool], None]:
        yield {
            "app_specific": True,
            "overridden": "app",
        }