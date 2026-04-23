def test_path_bool_42():
    response = client.get("/path/bool/42")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "bool_parsing",
                "loc": ["path", "item_id"],
                "msg": "Input should be a valid boolean, unable to interpret input",
                "input": "42",
            }
        ]
    }