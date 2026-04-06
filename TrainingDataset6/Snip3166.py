def test_query_model_with_alias():
    client = TestClient(app)
    response = client.get("/query", params={"param_alias": "value"})
    assert response.status_code == 200, response.text
    assert response.json() == {"param": "value"}