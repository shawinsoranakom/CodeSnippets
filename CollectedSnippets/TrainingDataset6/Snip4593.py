def test_cookie_param_model_invalid(client: TestClient):
    response = client.get("/items/")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["cookie", "session_id"],
                "msg": "Field required",
                "input": {},
            }
        ]
    }