def test_required_list_alias_by_alias(path: str):
    client = TestClient(app)
    response = client.get(f"{path}?p_alias=hello&p_alias=world")
    assert response.status_code == 200, response.text
    assert response.json() == {"p": ["hello", "world"]}