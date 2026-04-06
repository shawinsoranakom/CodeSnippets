def test_query_nonregexquery():
    client = get_client()
    response = client.post("/items/", data={"q": "nonregexquery"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "string_pattern_mismatch",
                "loc": ["body", "q"],
                "msg": "String should match pattern '^fixedquery$'",
                "input": "nonregexquery",
                "ctx": {"pattern": "^fixedquery$"},
            }
        ]
    }