def test_optional_list(path: str):
    client = TestClient(app)
    response = client.post(path, files=[("p", b"hello"), ("p", b"world")])
    assert response.status_code == 200
    assert response.json() == {"file_size": [5, 5]}