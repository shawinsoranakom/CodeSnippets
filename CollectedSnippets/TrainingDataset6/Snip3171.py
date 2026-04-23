def test_cookie_model_with_alias_by_name():
    client = TestClient(app)
    client.cookies.set("param", "value")
    response = client.get("/cookie")
    assert response.status_code == 422, response.text
    details = response.json()
    assert details["detail"][0]["input"] == {"param": "value"}