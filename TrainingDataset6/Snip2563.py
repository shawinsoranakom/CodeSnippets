def test_two_scopes() -> None:
    response = client.get("/two-scopes")
    assert response.status_code == 200
    data = response.json()
    assert data["func_is_open"] is False
    assert data["req_is_open"] is True