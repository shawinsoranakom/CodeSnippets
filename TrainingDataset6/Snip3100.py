def test_query_int_query_42_5():
    response = client.get("/query/int?query=42.5")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["query", "query"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "42.5",
            }
        ]
    }