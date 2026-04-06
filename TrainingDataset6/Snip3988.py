def test_get(client: TestClient):
    response = client.get("/")
    assert response.json() == {"$ref": "some-ref"}