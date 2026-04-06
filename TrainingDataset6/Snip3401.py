def test_optional_list_alias_and_validation_alias_missing(path: str):
    client = TestClient(app)
    response = client.post(path)
    assert response.status_code == 200
    assert response.json() == {"file_size": None}