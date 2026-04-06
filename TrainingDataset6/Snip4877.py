def test_get_items(item_id, expected_response):
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200, response.text
    assert response.json() == expected_response