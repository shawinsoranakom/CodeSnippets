def test_post_body_extra_form(client: TestClient):
    response = client.post(
        "/login/", data={"username": "Foo", "password": "secret", "extra": "extra"}
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "extra_forbidden",
                "loc": ["body", "extra"],
                "msg": "Extra inputs are not permitted",
                "input": "extra",
            }
        ]
    }