def test_cookie_model_with_alias():
    client = TestClient(app)
    client.cookies.set("param_alias", "value")
    response = client.get("/cookie")
    assert response.status_code == 200, response.text
    assert response.json() == {"param": "value"}