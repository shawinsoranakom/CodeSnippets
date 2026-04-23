def test_lax_accepts_json_content_type():
    response = client_lax.post("/items/", json={"key": "value"})
    assert response.status_code == 200
    assert response.json() == {"key": "value"}