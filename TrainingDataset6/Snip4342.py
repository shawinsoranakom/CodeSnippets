def test_default_router_inherits_strict_from_app():
    response = client.post("/default/items/", content='{"key": "value"}')
    assert response.status_code == 422