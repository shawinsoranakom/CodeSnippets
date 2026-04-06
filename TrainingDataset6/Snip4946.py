def test_query_param_model(client: TestClient):
    response = client.get(
        "/items/",
        params={
            "limit": 10,
            "offset": 5,
            "order_by": "updated_at",
            "tags": ["tag1", "tag2"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "limit": 10,
        "offset": 5,
        "order_by": "updated_at",
        "tags": ["tag1", "tag2"],
    }