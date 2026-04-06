def test_post_like_not_embeded(client: TestClient):
    response = client.put(
        "/items/5",
        json={
            "name": "Foo",
            "price": 50.5,
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": None,
                "loc": [
                    "body",
                    "item",
                ],
                "msg": "Field required",
                "type": "missing",
            },
        ],
    }