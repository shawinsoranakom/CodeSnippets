def test_invalid_data():
    response = client.post(
        "/form/",
        data={
            "username": "Rick",
            "lastname": "Sanchez",
            "age": "seventy",
            "tags": ["plumbus", "citadel"],
        },
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["body", "age"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "seventy",
            }
        ]
    }