def test_cookie_param_model_extra(client: TestClient):
    with client as c:
        c.cookies.set("session_id", "123")
        c.cookies.set("extra", "track-me-here-too")
        response = c.get("/items/")
    assert response.status_code == 422
    assert response.json() == snapshot(
        {
            "detail": [
                {
                    "type": "extra_forbidden",
                    "loc": ["cookie", "extra"],
                    "msg": "Extra inputs are not permitted",
                    "input": "track-me-here-too",
                }
            ]
        }
    )