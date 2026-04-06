def test_query_params_str_validations_q_short(client: TestClient):
    response = client.get("/items/", params={"q": "fa"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "string_too_short",
                "loc": ["query", "q"],
                "msg": "String should have at least 3 characters",
                "input": "fa",
                "ctx": {"min_length": 3},
            }
        ]
    }