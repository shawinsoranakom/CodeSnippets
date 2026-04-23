def test_query_params_str_validations_item_query_nonregexquery(client: TestClient):
    response = client.get("/items/", params={"item-query": "nonregexquery"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "string_pattern_mismatch",
                "loc": ["query", "item-query"],
                "msg": "String should match pattern '^fixedquery$'",
                "input": "nonregexquery",
                "ctx": {"pattern": "^fixedquery$"},
            }
        ]
    }