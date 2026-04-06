def test_post_validation_error():
    response = client.post("/items/", json={"title": "towel", "size": "XL"})
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["body", "size"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "XL",
            }
        ],
        "body": {"title": "towel", "size": "XL"},
    }