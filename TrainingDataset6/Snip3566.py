def test_optional_list_validation_alias_by_name(path: str):
    client = TestClient(app)
    response = client.get(path, headers=[("p", "hello"), ("p", "world")])
    assert response.status_code == 200
    assert response.json() == {"p": None}