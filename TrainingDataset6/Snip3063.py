def test_path_param_ge_int_2():
    response = client.get("/path/param-ge-int/2")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "greater_than_equal",
                "loc": ["path", "item_id"],
                "msg": "Input should be greater than or equal to 3",
                "input": "2",
                "ctx": {"ge": 3},
            }
        ]
    }