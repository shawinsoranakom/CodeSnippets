def test_optional_alias_and_validation_alias_by_validation_alias(path: str):
    client = TestClient(app)
    response = client.get(f"{path}?p_val_alias=hello")
    assert response.status_code == 200
    assert response.json() == {"p": "hello"}