def test_get(client: TestClient):
    response = client.get("/")
    assert response.json() == {"custom_field": [1.0, 2.0, 3.0]}