def test_post_no_item(client: TestClient):
    response = client.put("/items/5", json={"user": {"username": "johndoe"}})
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