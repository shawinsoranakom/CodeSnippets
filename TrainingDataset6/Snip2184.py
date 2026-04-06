def get_client(request):
    separate_input_output_schemas = request.param
    app = FastAPI(separate_input_output_schemas=separate_input_output_schemas)

    from pydantic import BaseModel, computed_field

    class Rectangle(BaseModel):
        width: int
        length: int

        @computed_field
        @property
        def area(self) -> int:
            return self.width * self.length

    @app.get("/")
    def read_root() -> Rectangle:
        return Rectangle(width=3, length=4)

    @app.get("/responses", responses={200: {"model": Rectangle}})
    def read_responses() -> Rectangle:
        return Rectangle(width=3, length=4)

    client = TestClient(app)
    return client