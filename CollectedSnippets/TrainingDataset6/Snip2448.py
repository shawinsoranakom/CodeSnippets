def test_parameterless_with_scopes():
    response = client.get(
        "/parameterless-with-scopes", headers={"authorization": "Bearer token"}
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok"}