def test_validator_is_cloned(client: TestClient):
    with pytest.raises(ResponseValidationError) as err:
        client.get("/model/modelX")
    assert err.value.errors() == [
        {
            "type": "value_error",
            "loc": ("response", "name"),
            "msg": "Value error, name must end in A",
            "input": "modelX",
            "ctx": {"error": HasRepr("ValueError('name must end in A')")},
        }
    ]