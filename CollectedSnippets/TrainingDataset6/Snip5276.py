def test_app(client: TestClient):
    response = client.get("/info")
    data = response.json()
    assert data == {
        "app_name": "Awesome API",
        "admin_email": "admin@example.com",
        "items_per_user": 50,
    }