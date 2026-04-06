def test_get_no_headers_items(client: TestClient):
    response = client.get("/items/")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["header", "x-token"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["header", "x-key"],
                "msg": "Field required",
                "input": None,
            },
        ]
    }