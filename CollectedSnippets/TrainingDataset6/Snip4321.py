def test_default_strict_rejects_no_content_type():
    response = client_default.post("/items/", content='{"key": "value"}')
    assert response.status_code == 422