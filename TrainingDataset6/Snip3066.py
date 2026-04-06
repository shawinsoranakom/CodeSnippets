def test_path_param_lt_gt_int_4():
    response = client.get("/path/param-lt-gt-int/4")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "less_than",
                "loc": ["path", "item_id"],
                "msg": "Input should be less than 3",
                "input": "4",
                "ctx": {"lt": 3},
            }
        ]
    }