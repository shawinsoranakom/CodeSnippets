def test_optional_str(path: str):
    client = TestClient(app)
    response = client.get(f"{path}?p=hello")
    assert response.status_code == 200
    assert response.json() == {"p": "hello"}