def get_client():
    from pydantic import (
        BaseModel,
        ConfigDict,
        PlainSerializer,
        TypeAdapter,
        WithJsonSchema,
    )

    class FakeNumpyArray:
        def __init__(self):
            self.data = [1.0, 2.0, 3.0]

    FakeNumpyArrayPydantic = Annotated[
        FakeNumpyArray,
        WithJsonSchema(TypeAdapter(list[float]).json_schema()),
        PlainSerializer(lambda v: v.data),
    ]

    class MyModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        custom_field: FakeNumpyArrayPydantic

    app = FastAPI()

    @app.get("/")
    def test() -> MyModel:
        return MyModel(custom_field=FakeNumpyArray())

    client = TestClient(app)
    return client