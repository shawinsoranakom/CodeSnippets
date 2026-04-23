def test_parameterless_without_scopes():
    response = client.get(
        "/parameterless-without-scopes", headers={"authorization": "Bearer token"}
    )
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "a or b not in scopes"}