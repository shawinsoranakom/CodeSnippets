def test_query_param_required_int_query_foo():
    response = client.get("/query/param-required/int?query=foo")
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