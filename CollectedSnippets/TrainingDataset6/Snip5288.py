def test_settings(app):
    client = TestClient(app)
    response = client.get("/info")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "app_name": "Awesome API",
        "admin_email": "admin@example.com",
        "items_per_user": 50,
    }