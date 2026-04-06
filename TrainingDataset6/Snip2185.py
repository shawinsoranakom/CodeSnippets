def test_get(client: TestClient, path: str):
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert response.json() == {"width": 3, "length": 4, "area": 12}