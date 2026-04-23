def test_items_with_no_token_jessica(client: TestClient):
    response = client.get("/items", headers={"X-Token": "fake-super-secret-token"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "token"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }