def test_endpoint_works(client: TestClient):
    response = client.post("/", json=[1, 2, 3])
    assert response.json() == 6