def test_strict_inner_on_lax_app_rejects_no_content_type():
    response = client_nested.post("/outer/strict/items/", content='{"key": "value"}')
    assert response.status_code == 422