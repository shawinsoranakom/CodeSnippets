def _make_ujson_app() -> FastAPI:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FastAPIDeprecationWarning)
        app = FastAPI(default_response_class=UJSONResponse)

    @app.get("/items")
    def get_items() -> Item:
        return Item(name="widget", price=9.99)

    return app