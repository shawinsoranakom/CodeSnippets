def test_read_items(client: TestClient, path, expected_response):
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert response.json() == expected_response