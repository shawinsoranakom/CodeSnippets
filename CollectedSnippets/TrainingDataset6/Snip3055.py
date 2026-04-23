def test_path_param_gt_int_2():
    response = client.get("/path/param-gt-int/2")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "greater_than",
                "loc": ["path", "item_id"],
                "msg": "Input should be greater than 3",
                "input": "2",
                "ctx": {"gt": 3},
            }
        ]
    }