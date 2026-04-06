def lifespan(app: FastAPI) -> Generator[None, None, None]:
        state.app_startup = True
        yield
        state.app_shutdown = True