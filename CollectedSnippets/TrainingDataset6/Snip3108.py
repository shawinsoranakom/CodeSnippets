def test_query_int_default_query_foo():
    response = client.get("/query/int/default?query=foo")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["query", "query"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "foo",
            }
        ]
    }