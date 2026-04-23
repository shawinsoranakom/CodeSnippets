def test_path_param_le_42():
    response = client.get("/path/param-le/42")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "less_than_equal",
                "loc": ["path", "item_id"],
                "msg": "Input should be less than or equal to 3",
                "input": "42",
                "ctx": {"le": 3.0},
            }
        ]
    }