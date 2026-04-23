def test_optional_alias_missing():
    client = TestClient(app)
    response = client.post("/optional-alias")
    assert response.status_code == 200
    assert response.json() == {"p": None}