def test_optional_list_str_missing_empty_dict(path: str):
    client = TestClient(app)
    response = client.post(path, json={})
    assert response.status_code == 200, response.text
    assert response.json() == {"p": None}