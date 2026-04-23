def test_get_me_no_credentials(client: TestClient):
    response = client.get("/me")
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}