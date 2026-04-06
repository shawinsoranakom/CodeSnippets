def test_strict_login_no_grant_type():
    response = client.post("/login", data={"username": "johndoe", "password": "secret"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "grant_type"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }