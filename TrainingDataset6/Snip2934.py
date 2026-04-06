def get_app_client(separate_input_output_schemas: bool = True) -> TestClient:
    app = FastAPI(separate_input_output_schemas=separate_input_output_schemas)

    @app.post("/items/", responses={402: {"model": Item}})
    def create_item(item: Item) -> Item:
        return item

    @app.post("/items-list/")
    def create_item_list(item: list[Item]):
        return item

    @app.get("/items/")
    def read_items() -> list[Item]:
        return [
            Item(
                name="Portal Gun",
                description="Device to travel through the multi-rick-verse",
                sub=SubItem(subname="subname"),
            ),
            Item(name="Plumbus"),
        ]

    @app.post("/with-computed-field/")
    def create_with_computed_field(
        with_computed_field: WithComputedField,
    ) -> WithComputedField:
        return with_computed_field

    client = TestClient(app)
    return client