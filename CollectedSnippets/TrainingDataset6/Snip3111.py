def test_query_param_required():
    response = client.get("/query/param-required")
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