def test_query_list_default_empty():
    response = client.get("/query/list-default/")
    assert response.status_code == 200
    assert response.json() == []