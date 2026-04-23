def test_post_body_json(client: TestClient):
    response = client.post("/login/", json={"username": "Foo", "password": "secret"})
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "username"],
                "msg": "Field required",
                "input": {},
            },
            {
                "type": "missing",
                "loc": ["body", "password"],
                "msg": "Field required",
                "input": {},
            },
        ]
    }