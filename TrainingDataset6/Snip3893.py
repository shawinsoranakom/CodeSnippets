def test_invalid_response_model_sub_type_in_responses_raises():
    with pytest.raises(FastAPIError):
        app = FastAPI()

        @app.get("/", responses={"500": {"model": list[NonPydanticModel]}})
        def read_root():
            pass