def test_read_items_missing_q(client: TestClient):
    response = client.get("/items/42")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["query", "q"],
                "input": None,
                "msg": "Field required",
                "type": "missing",
            }
        ]
    }