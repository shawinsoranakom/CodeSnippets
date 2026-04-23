def test_get_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"hello world": "ba"}