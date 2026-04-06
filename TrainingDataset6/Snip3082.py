def test_raises_pydantic_v1_model_in_union() -> None:
    class ModelV1A(BaseModel):
        name: str

    app = FastAPI()

    with pytest.raises(PydanticV1NotSupportedError):

        @app.post("/union")
        def endpoint(data: dict | ModelV1A):  # pragma: no cover
            return data