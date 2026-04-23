def test_items_with_missing_x_token_header(client: TestClient):
    response = client.get("/items?token=jessica")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["header", "x-token"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }