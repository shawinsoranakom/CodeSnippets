def test_required_alias_by_alias(path: str):
    client = TestClient(app)
    response = client.post(path, files=[("p_alias", b"hello")])
    assert response.status_code == 200, response.text
    assert response.json() == {"file_size": 5}