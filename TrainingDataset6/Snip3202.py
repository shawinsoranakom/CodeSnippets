def test_optional_list_str(path: str):
    client = TestClient(app)
    response = client.post(path, json={"p": ["hello", "world"]})
    assert response.status_code == 200
    assert response.json() == {"p": ["hello", "world"]}