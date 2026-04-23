def test_success(path: str):
    client = TestClient(app)
    response = client.get(f"{path}/hello")
    assert response.status_code == 200, response.text
    assert response.json() == {"p": "hello"}