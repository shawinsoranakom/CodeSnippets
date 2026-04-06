def test_query_params_str_validations_q_nonregexquery(client: TestClient):
    response = client.get("/items/", params={"q": "nonregexquery"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "string_pattern_mismatch",
                "loc": ["query", "q"],
                "msg": "String should match pattern '^fixedquery$'",
                "input": "nonregexquery",
                "ctx": {"pattern": "^fixedquery$"},
            }
        ]
    }