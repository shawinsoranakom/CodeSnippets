def test_default_router_accepts_json_content_type():
    response = client.post("/default/items/", json={"key": "value"})
    assert response.status_code == 200