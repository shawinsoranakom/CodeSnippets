def test_read_user_item(client: TestClient, path, expected_json):
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == expected_json