def test_raises_pydantic_v1_model_in_return_type() -> None:
    class ReturnModelV1(BaseModel):
        name: str

    app = FastAPI()

    with pytest.raises(PydanticV1NotSupportedError):

        @app.get("/return")
        def endpoint() -> ReturnModelV1:  # pragma: no cover
            return ReturnModelV1(name="test")