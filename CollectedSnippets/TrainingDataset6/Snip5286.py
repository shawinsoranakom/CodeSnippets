def test_endpoint(main_mod: ModuleType, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    client = TestClient(main_mod.app)
    response = client.get("/info")
    assert response.status_code == 200
    assert response.json() == {
        "app_name": "Awesome API",
        "admin_email": "admin@example.com",
        "items_per_user": 50,
    }