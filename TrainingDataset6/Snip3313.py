def test_required_str(path: str):
    client = TestClient(app)
    client.cookies.set("p", "hello")
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == {"p": "hello"}