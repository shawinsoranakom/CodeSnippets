def test_cookie_param_model_extra(client: TestClient):
    with client as c:
        c.cookies.set("session_id", "123")
        c.cookies.set("extra", "track-me-here-too")
        response = c.get("/items/")
    assert response.status_code == 200
    assert response.json() == snapshot(
        {"session_id": "123", "fatebook_tracker": None, "googall_tracker": None}
    )