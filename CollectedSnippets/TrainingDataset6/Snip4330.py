def test_default_inner_accepts_json_content_type():
    response = client_nested.post("/outer/default/items/", json={"key": "value"})
    assert response.status_code == 200