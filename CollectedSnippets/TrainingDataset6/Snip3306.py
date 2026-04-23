def test_optional_alias_and_validation_alias_by_name(path: str):
    client = TestClient(app)
    client.cookies.set("p", "hello")
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == {"p": None}