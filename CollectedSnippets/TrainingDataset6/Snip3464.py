def test_optional_list_alias_by_alias(path: str):
    client = TestClient(app)
    response = client.post(path, data={"p_alias": ["hello", "world"]})
    assert response.status_code == 200
    assert response.json() == {"p": ["hello", "world"]}