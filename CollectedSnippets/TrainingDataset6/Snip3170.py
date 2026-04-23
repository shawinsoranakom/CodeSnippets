def test_header_model_with_alias_by_name():
    client = TestClient(app)
    response = client.get("/header", headers={"param": "value"})
    assert response.status_code == 422, response.text
    details = response.json()
    assert details["detail"][0]["input"] == IsPartialDict({"param": "value"})