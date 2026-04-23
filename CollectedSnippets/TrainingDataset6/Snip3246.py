def test_optional_validation_alias_missing():
    client = TestClient(app)
    response = client.post("/optional-validation-alias")
    assert response.status_code == 200
    assert response.json() == {"p": None}