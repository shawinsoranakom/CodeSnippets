def test_root_with_no_token(client: TestClient):
    response = client.get("/")
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