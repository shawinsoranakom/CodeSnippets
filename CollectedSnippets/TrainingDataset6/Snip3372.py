def test_optional_validation_alias_by_name(path: str):
    client = TestClient(app)
    response = client.post(path, files=[("p", b"hello")])
    assert response.status_code == 200, response.text
    assert response.json() == {"file_size": None}