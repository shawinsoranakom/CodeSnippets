def test_multi_query_incorrect():
    response = client.get("/items/?q=five&q=six")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["query", "q", 0],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "five",
            },
            {
                "type": "int_parsing",
                "loc": ["query", "q", 1],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "six",
            },
        ]
    }