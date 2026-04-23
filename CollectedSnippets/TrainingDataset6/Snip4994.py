def test_query_params_str_validations_q_query(client: TestClient):
    response = client.get("/items/", params={"q": "query"})
    assert response.status_code == 200
    assert response.json() == {
        "items": [{"item_id": "Foo"}, {"item_id": "Bar"}],
        "q": "query",
    }