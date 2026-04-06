def test_raises_pydantic_v1_model_in_additional_responses_model() -> None:
    class ErrorModelV1(BaseModel):
        detail: str

    app = FastAPI()

    with pytest.raises(PydanticV1NotSupportedError):

        @app.get(
            "/responses", response_model=None, responses={400: {"model": ErrorModelV1}}
        )
        def endpoint():  # pragma: no cover
            return {"ok": True}