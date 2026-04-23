def test_raises_pydantic_v1_model_in_endpoint_param() -> None:
    class ParamModelV1(BaseModel):
        name: str

    app = FastAPI()

    with pytest.raises(PydanticV1NotSupportedError):

        @app.post("/param")
        def endpoint(data: ParamModelV1):  # pragma: no cover
            return data