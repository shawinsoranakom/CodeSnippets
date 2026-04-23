def test_query_params_str_validations_q_too_long(client: TestClient):
    response = client.get("/items/", params={"q": "q" * 51})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "string_too_long",
                "loc": ["query", "q"],
                "msg": "String should have at most 50 characters",
                "input": "q" * 51,
                "ctx": {"max_length": 50},
            }
        ]
    }