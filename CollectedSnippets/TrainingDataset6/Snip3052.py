def test_path_param_lt_int_42():
    response = client.get("/path/param-lt-int/42")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "less_than",
                "loc": ["path", "item_id"],
                "msg": "Input should be less than 3",
                "input": "42",
                "ctx": {"lt": 3},
            }
        ]
    }