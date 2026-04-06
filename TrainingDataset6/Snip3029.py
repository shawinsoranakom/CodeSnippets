def test_path_param_min_maxlength_f():
    response = client.get("/path/param-min_maxlength/f")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "string_too_short",
                "loc": ["path", "item_id"],
                "msg": "String should have at least 2 characters",
                "input": "f",
                "ctx": {"min_length": 2},
            }
        ]
    }