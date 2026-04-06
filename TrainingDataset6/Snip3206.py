def test_optional_list_alias_missing():
    client = TestClient(app)
    response = client.post("/optional-list-alias")
    assert response.status_code == 200, response.text
    assert response.json() == {"p": None}