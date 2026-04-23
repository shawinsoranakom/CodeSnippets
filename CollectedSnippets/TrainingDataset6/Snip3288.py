def test_optional_str_missing(path: str):
    client = TestClient(app)
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == {"p": None}