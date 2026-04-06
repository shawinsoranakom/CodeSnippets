def test_path_bool_42_5():
    response = client.get("/path/bool/42.5")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "bool_parsing",
                "loc": ["path", "item_id"],
                "msg": "Input should be a valid boolean, unable to interpret input",
                "input": "42.5",
            }
        ]
    }