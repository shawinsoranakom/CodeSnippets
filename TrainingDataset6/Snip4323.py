def test_lax_accepts_no_content_type():
    response = client_lax.post("/items/", content='{"key": "value"}')
    assert response.status_code == 200
    assert response.json() == {"key": "value"}