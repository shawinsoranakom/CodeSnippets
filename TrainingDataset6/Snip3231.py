def test_optional_str_missing():
    client = TestClient(app)
    response = client.post("/optional-str")
    assert response.status_code == 200, response.text
    assert response.json() == {"p": None}