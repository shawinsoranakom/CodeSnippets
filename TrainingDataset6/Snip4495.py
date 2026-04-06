def test_post_no_body(client: TestClient):
    response = client.put("/items/5", json=None)
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