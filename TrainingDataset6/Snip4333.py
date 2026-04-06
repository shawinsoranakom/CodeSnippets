def test_lax_outer_on_strict_app_accepts_no_content_type():
    response = client_mixed.post("/outer/items/", content='{"key": "value"}')
    assert response.status_code == 200
    assert response.json() == {"key": "value"}