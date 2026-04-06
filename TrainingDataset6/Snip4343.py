def test_lax_router_accepts_json_content_type():
    response = client.post("/lax/items/", json={"key": "value"})
    assert response.status_code == 200