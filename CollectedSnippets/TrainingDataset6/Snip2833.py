def test_json_encoder_error_with_pydanticv1():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        from pydantic import v1

    class ModelV1(v1.BaseModel):
        name: str

    data = ModelV1(name="test")
    with pytest.raises(PydanticV1NotSupportedError):
        jsonable_encoder(data)