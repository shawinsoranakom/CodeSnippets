def test_post_no_user(client: TestClient):
    response = client.put("/items/5", json={"item": {"name": "Foo", "price": 50.5}})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": None,
                "loc": [
                    "body",
                    "user",
                ],
                "msg": "Field required",
                "type": "missing",
            },
        ],
    }