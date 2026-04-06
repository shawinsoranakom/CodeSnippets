def test_owner_error(client: TestClient):
    response = client.get("/items/plumbus")
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Owner error: Rick"}