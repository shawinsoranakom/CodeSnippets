def test_get(client: TestClient):
    response = client.get("/users")
    assert response.json() == {"username": "alice", "role": "admin"}