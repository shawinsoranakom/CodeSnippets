def test_path_param_lt0_0():
    response = client.get("/path/param-lt0/0")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "less_than",
                "loc": ["path", "item_id"],
                "msg": "Input should be less than 0",
                "input": "0",
                "ctx": {"lt": 0.0},
            }
        ]
    }