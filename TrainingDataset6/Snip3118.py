def test_query_list_empty():
    response = client.get("/query/list/")
    assert response.status_code == 422