def test_optional_alias_and_validation_alias_by_alias(path: str):
    client = TestClient(app)
    client.cookies.set("p_alias", "hello")
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == {"p": None}