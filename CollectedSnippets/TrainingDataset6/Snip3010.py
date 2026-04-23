def test_path_float_True():
    response = client.get("/path/float/True")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "float_parsing",
                "loc": ["path", "item_id"],
                "msg": "Input should be a valid number, unable to parse string as a number",
                "input": "True",
            }
        ]
    }