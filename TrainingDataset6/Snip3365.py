def test_optional_alias_missing(path: str):
    client = TestClient(app)
    response = client.post(path)
    assert response.status_code == 200
    assert response.json() == {"file_size": None}