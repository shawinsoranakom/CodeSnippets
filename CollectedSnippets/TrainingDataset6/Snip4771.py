def test_get_validation_error():
    response = client.get("/items/foo")
    assert response.status_code == 400, response.text
    assert "Validation errors:" in response.text
    assert "Field: ('path', 'item_id')" in response.text