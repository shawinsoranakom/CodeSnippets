def test_path_param_gt0_0():
    response = client.get("/path/param-gt0/0")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "greater_than",
                "loc": ["path", "item_id"],
                "msg": "Input should be greater than 0",
                "input": "0",
                "ctx": {"gt": 0.0},
            }
        ]
    }