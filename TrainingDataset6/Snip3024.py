def test_path_param_minlength_fo():
    response = client.get("/path/param-minlength/fo")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "string_too_short",
                "loc": ["path", "item_id"],
                "msg": "String should have at least 3 characters",
                "input": "fo",
                "ctx": {"min_length": 3},
            }
        ]
    }