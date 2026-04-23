def test_sub() -> None:
    response = client.get("/sub")
    assert response.status_code == 200
    data = response.json()
    assert data["named_session_open"] is True
    assert data["session_open"] is True