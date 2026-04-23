def test_get(client: TestClient):
    response = client.get("/")
    assert response.json() == {"message": "Not timed"}
    assert "X-Response-Time" not in response.headers