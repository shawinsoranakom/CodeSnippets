def test_get_items():
    response = client.get("/items/1")
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": 1}