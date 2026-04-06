def test_optional_list_validation_alias_missing_empty_dict(path: str):
    client = TestClient(app)
    response = client.post(path, json={})
    assert response.status_code == 200, response.text
    assert response.json() == {"p": None}