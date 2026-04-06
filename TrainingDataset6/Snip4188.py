def test_security_scopes_dependency_called_once(
    client: TestClient, call_counter: dict[str, int]
):
    response = client.get("/")

    assert response.status_code == 200
    assert call_counter["count"] == 1