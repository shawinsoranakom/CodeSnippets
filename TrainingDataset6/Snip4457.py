def test_post_with_none(client: TestClient):
    response = client.post("/items/", json=None)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }