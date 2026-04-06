def test_query_params_str_validations_empty_str(client: TestClient):
    response = client.get("/items/?q=")
    assert response.status_code == 200
    assert response.json() == {  # pragma: no cover
        "items": [{"item_id": "Foo"}, {"item_id": "Bar"}],
    }