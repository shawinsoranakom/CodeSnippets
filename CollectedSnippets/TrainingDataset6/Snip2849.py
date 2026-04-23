def test_encode_pydantic_undefined():
    data = {"value": Undefined}
    assert jsonable_encoder(data) == {"value": None}