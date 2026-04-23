def test_post_missing_required_field_in_user(client: TestClient):
    response = client.put(
        "/items/5",
        json={"item": {"name": "Foo", "price": 50.5}, "user": {"ful_name": "John Doe"}},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": {"ful_name": "John Doe"},
                "loc": [
                    "body",
                    "user",
                    "username",
                ],
                "msg": "Field required",
                "type": "missing",
            },
        ],
    }