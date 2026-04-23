def test_optional_alias_by_name(path: str):
    client = TestClient(app)
    response = client.post(path, data={"p": "hello"})
    assert response.status_code == 200
    assert response.json() == {"p": None}