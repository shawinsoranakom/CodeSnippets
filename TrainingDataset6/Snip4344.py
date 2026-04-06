def test_strict_router_accepts_json_content_type():
    response = client.post("/strict/items/", json={"key": "value"})
    assert response.status_code == 200