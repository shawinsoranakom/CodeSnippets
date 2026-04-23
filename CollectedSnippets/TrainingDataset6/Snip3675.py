def test_optional_list_alias_and_validation_alias_by_alias(path: str):
    client = TestClient(app)
    response = client.get(f"{path}?p_alias=hello&p_alias=world")
    assert response.status_code == 200
    assert response.json() == {"p": None}