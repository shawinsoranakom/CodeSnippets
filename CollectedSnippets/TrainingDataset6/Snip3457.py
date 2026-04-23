def test_optional_list_str_missing(path: str):
    client = TestClient(app)
    response = client.post(path)
    assert response.status_code == 200, response.text
    assert response.json() == {"p": None}