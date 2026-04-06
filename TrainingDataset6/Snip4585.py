def test_cookie_param_model(client: TestClient):
    with client as c:
        c.cookies.set("session_id", "123")
        c.cookies.set("fatebook_tracker", "456")
        c.cookies.set("googall_tracker", "789")
        response = c.get("/items/")
    assert response.status_code == 200
    assert response.json() == {
        "session_id": "123",
        "fatebook_tracker": "456",
        "googall_tracker": "789",
    }