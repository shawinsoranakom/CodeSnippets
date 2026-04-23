def test_raises_pydantic_v1_model_in_sequence() -> None:
    class ModelV1A(BaseModel):
        name: str

    app = FastAPI()

    with pytest.raises(PydanticV1NotSupportedError):

        @app.post("/sequence")
        def endpoint(data: list[ModelV1A]):  # pragma: no cover
            return data