def test_get_data(client: TestClient):
    response = client.get("/data")
    assert response.status_code == 200, response.text
    assert response.json() == {"description": "A plumbus", "data": "aGVsbG8="}