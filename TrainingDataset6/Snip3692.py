def test_optional_validation_alias_by_name(path: str):
    client = TestClient(app)
    response = client.get(f"{path}?p=hello")
    assert response.status_code == 200
    assert response.json() == {"p": None}