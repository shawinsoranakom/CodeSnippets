def test_path_param_lt_gt_0():
    response = client.get("/path/param-lt-gt/0")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "greater_than",
                "loc": ["path", "item_id"],
                "msg": "Input should be greater than 1",
                "input": "0",
                "ctx": {"gt": 1.0},
            }
        ]
    }