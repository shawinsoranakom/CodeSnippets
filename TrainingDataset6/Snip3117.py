def test_query_list():
    response = client.get("/query/list/?device_ids=1&device_ids=2")
    assert response.status_code == 200
    assert response.json() == [1, 2]