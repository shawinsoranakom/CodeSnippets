def test_optional_list_str(path: str):
    client = TestClient(app)
    response = client.get(path, headers=[("p", "hello"), ("p", "world")])
    assert response.status_code == 200
    assert response.json() == {"p": ["hello", "world"]}