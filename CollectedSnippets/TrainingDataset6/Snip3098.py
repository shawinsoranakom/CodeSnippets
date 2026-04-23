def test_query_int():
    response = client.get("/query/int")
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