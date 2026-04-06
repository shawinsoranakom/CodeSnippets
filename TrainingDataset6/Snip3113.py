def test_query_param_required_int():
    response = client.get("/query/param-required/int")
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