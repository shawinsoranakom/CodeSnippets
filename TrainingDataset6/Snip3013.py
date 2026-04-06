def test_path_bool_foobar():
    response = client.get("/path/bool/foobar")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "bool_parsing",
                "loc": ["path", "item_id"],
                "msg": "Input should be a valid boolean, unable to interpret input",
                "input": "foobar",
            }
        ]
    }