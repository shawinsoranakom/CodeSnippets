def test_path_operation():
    response = client.get("/items/foo")
    assert response.status_code == 200
    assert response.json() == {"client_host": "testclient", "item_id": "foo"}