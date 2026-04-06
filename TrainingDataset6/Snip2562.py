def test_request_scope() -> None:
    response = client.get("/request-scope")
    assert response.status_code == 200
    data = response.json()
    assert data["is_open"] is True