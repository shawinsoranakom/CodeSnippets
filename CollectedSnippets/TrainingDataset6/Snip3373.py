def test_optional_validation_alias_by_validation_alias(path: str):
    client = TestClient(app)
    response = client.post(path, files=[("p_val_alias", b"hello")])
    assert response.status_code == 200, response.text
    assert response.json() == {"file_size": 5}