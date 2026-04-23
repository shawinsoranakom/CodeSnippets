def test_get_invalid_item(client: TestClient):
    response = client.get("/items?id=wtf-yes")
    assert response.status_code == 422, response.text
    assert response.json() == snapshot(
        {
            "detail": [
                {
                    "type": "value_error",
                    "loc": ["query", "id"],
                    "msg": 'Value error, Invalid ID format, it must start with "isbn-" or "imdb-"',
                    "input": "wtf-yes",
                    "ctx": {"error": {}},
                }
            ]
        }
    )