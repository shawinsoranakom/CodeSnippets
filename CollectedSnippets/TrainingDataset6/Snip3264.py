def test_required_str(path: str):
    client = TestClient(app)
    response = client.post(path, json={"p": "hello"})
    assert response.status_code == 200
    assert response.json() == {"p": "hello"}