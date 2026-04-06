def test_warn_duplicate_operation_id():
    def broken_operation_id(route: APIRoute):
        return "foo"

    app = FastAPI(generate_unique_id_function=broken_operation_id)

    @app.post("/")
    def post_root(item1: Item):
        return item1  # pragma: nocover

    @app.post("/second")
    def post_second(item1: Item):
        return item1  # pragma: nocover

    @app.post("/third")
    def post_third(item1: Item):
        return item1  # pragma: nocover

    client = TestClient(app)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        client.get("/openapi.json")
        assert len(w) >= 2
        duplicate_warnings = [
            warning for warning in w if issubclass(warning.category, UserWarning)
        ]
        assert len(duplicate_warnings) > 0
        assert "Duplicate Operation ID" in str(duplicate_warnings[0].message)