def test_invalid_sequence():
    with pytest.raises(
        AssertionError,
        match="Query parameter 'q' must be one of the supported types",
    ):
        app = FastAPI()

        class Item(BaseModel):
            title: str

        @app.get("/items/")
        def read_items(q: list[Item] = Query(default=None)):
            pass