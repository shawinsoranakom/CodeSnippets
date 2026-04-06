def test_default_strict_accepts_json_content_type():
    response = client_default.post("/items/", json={"key": "value"})
    assert response.status_code == 200
    assert response.json() == {"key": "value"}