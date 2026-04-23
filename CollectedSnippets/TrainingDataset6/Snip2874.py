def test_put_incorrect_body_multiple():
    response = client.post("/items/", json=[{"age": "five"}, {"age": "six"}])
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", 0, "name"],
                "msg": "Field required",
                "input": {"age": "five"},
            },
            {
                "type": "decimal_parsing",
                "loc": ["body", 0, "age"],
                "msg": "Input should be a valid decimal",
                "input": "five",
            },
            {
                "type": "missing",
                "loc": ["body", 1, "name"],
                "msg": "Field required",
                "input": {"age": "six"},
            },
            {
                "type": "decimal_parsing",
                "loc": ["body", 1, "age"],
                "msg": "Input should be a valid decimal",
                "input": "six",
            },
        ]
    }