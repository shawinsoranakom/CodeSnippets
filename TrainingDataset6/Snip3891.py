def test_invalid_response_model_sub_type_raises():
    with pytest.raises(FastAPIError):
        app = FastAPI()

        @app.get("/", response_model=list[NonPydanticModel])
        def read_root():
            pass