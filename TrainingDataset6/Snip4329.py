def test_strict_inner_accepts_json_content_type():
    response = client_nested.post("/outer/strict/items/", json={"key": "value"})
    assert response.status_code == 200