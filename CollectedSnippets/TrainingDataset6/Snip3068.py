def test_path_param_lt_gt_int_2_7():
    response = client.get("/path/param-lt-gt-int/2.7")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["path", "item_id"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "2.7",
            }
        ]
    }