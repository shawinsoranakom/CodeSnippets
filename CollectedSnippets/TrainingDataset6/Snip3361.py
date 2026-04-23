def test_optional(path: str):
    client = TestClient(app)
    response = client.post(path, files=[("p", b"hello")])
    assert response.status_code == 200
    assert response.json() == {"file_size": 5}