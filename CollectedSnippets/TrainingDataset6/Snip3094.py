def test_query_not_declared_baz():
    response = client.get("/query?not_declared=baz")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "query"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }