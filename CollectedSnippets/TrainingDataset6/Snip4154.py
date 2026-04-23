def test_strict_login_incorrect_grant_type(grant_type: str):
    response = client.post(
        "/login",
        data={"username": "johndoe", "password": "secret", "grant_type": grant_type},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "string_pattern_mismatch",
                "loc": ["body", "grant_type"],
                "msg": "String should match pattern '^password$'",
                "input": grant_type,
                "ctx": {"pattern": "^password$"},
            }
        ]
    }