def test_cookie_param_model_defaults(client: TestClient):
    with client as c:
        c.cookies.set("session_id", "123")
        response = c.get("/items/")
    assert response.status_code == 200
    assert response.json() == {
        "session_id": "123",
        "fatebook_tracker": None,
        "googall_tracker": None,
    }