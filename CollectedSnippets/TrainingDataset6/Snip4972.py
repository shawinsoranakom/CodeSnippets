def test_query_params_str_validations_q_empty_str(client: TestClient):
    response = client.get("/items/", params={"q": ""})
    assert response.status_code == 200
    assert response.json() == {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}