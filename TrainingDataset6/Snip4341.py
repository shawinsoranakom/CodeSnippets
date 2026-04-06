def test_strict_router_on_strict_app_rejects_no_content_type():
    response = client.post("/strict/items/", content='{"key": "value"}')
    assert response.status_code == 422