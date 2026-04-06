def test_post_with_no_data(client: TestClient):
    response = client.post("/items/", json={})
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