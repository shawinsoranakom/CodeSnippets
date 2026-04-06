def test_put_no_header(client: TestClient):
    response = client.put("/items/foo")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "token"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["header", "x-token"],
                "msg": "Field required",
                "input": None,
            },
        ]
    }