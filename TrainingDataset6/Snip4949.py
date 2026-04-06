def test_query_param_model_extra(client: TestClient):
    response = client.get(
        "/items/",
        params={
            "limit": 10,
            "offset": 5,
            "order_by": "updated_at",
            "tags": ["tag1", "tag2"],
            "tool": "plumbus",
        },
    )
    assert response.status_code == 422
    assert response.json() == snapshot(
        {
            "detail": [
                {
                    "type": "extra_forbidden",
                    "loc": ["query", "tool"],
                    "msg": "Extra inputs are not permitted",
                    "input": "plumbus",
                }
            ]
        }
    )