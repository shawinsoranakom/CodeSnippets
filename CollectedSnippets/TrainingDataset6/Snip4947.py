def test_query_param_model_defaults(client: TestClient):
    response = client.get("/items/")
    assert response.status_code == 200
    assert response.json() == {
        "limit": 100,
        "offset": 0,
        "order_by": "created_at",
        "tags": [],
    }