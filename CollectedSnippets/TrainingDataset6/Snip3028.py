def test_path_param_min_maxlength_foobar():
    response = client.get("/path/param-min_maxlength/foobar")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "string_too_long",
                "loc": ["path", "item_id"],
                "msg": "String should have at most 3 characters",
                "input": "foobar",
                "ctx": {"max_length": 3},
            }
        ]
    }