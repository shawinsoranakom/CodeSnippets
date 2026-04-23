def test_function_scope() -> None:
    response = client.get("/function-scope")
    assert response.status_code == 200
    data = response.json()
    assert data["is_open"] is False