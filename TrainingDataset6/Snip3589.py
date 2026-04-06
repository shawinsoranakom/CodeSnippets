def test_optional_validation_alias_missing(path: str):
    client = TestClient(app)
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == {"p": None}