def test_query_params_str_validations_item_query_nonregexquery():
    client = get_client()
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