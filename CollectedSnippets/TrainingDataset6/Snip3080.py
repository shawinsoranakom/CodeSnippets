def test_raises_pydantic_v1_model_in_response_model() -> None:
    class ResponseModelV1(BaseModel):
        name: str

    app = FastAPI()

    with pytest.raises(PydanticV1NotSupportedError):

        @app.get("/response-model", response_model=ResponseModelV1)
        def endpoint():  # pragma: no cover
            return {"name": "test"}