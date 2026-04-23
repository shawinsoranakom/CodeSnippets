def test_query_int_query_baz():
    response = client.get("/query/int?query=baz")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["query", "query"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "baz",
            }
        ]
    }