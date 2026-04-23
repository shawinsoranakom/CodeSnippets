def test_orjson_non_str_keys():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FastAPIDeprecationWarning)
        with client:
            response = client.get("/orjson_non_str_keys")
    assert response.json() == {"msg": "Hello World", "1": 1}