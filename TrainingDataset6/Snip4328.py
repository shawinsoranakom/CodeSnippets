def test_default_inner_inherits_lax_from_app():
    response = client_nested.post("/outer/default/items/", content='{"key": "value"}')
    assert response.status_code == 200
    assert response.json() == {"key": "value"}