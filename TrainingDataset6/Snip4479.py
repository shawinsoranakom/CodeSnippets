def test_put_with_no_data(client: TestClient):
    response = client.put("/items/123", json={})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "name"],
                "msg": "Field required",
                "input": {},
            },
            {
                "type": "missing",
                "loc": ["body", "price"],
                "msg": "Field required",
                "input": {},
            },
        ]
    }