def test_strict_inner_on_lax_outer_rejects_no_content_type():
    response = client_mixed.post("/outer/inner/items/", content='{"key": "value"}')
    assert response.status_code == 422