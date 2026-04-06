def test_regular_function_scope() -> None:
    response = client.get("/regular-function-scope")
    assert response.status_code == 200
    data = response.json()
    assert data["named_session_open"] is True
    assert data["session_open"] is False