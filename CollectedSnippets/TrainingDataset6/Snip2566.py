def test_named_function_scope() -> None:
    response = client.get("/named-function-scope")
    assert response.status_code == 200
    data = response.json()
    assert data["named_session_open"] is False
    assert data["session_open"] is False