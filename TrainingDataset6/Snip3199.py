def test_optional_list_str_missing():
    client = TestClient(app)
    response = client.post("/optional-list-str")
    assert response.status_code == 200, response.text
    assert response.json() == {"p": None}