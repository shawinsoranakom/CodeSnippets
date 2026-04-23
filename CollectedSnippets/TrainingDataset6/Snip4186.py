def app_fixture(call_counter: dict[str, int]):
    def get_db():
        call_counter["count"] += 1
        return f"db_{call_counter['count']}"

    def get_user(db: Annotated[str, Depends(get_db)]):
        return "user"

    app = FastAPI()

    @app.get("/")
    def endpoint(
        db: Annotated[str, Depends(get_db)],
        user: Annotated[str, Security(get_user, scopes=["read"])],
    ):
        return {"db": db}

    return app