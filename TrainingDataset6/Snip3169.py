def test_query_model_with_alias_by_name():
    client = TestClient(app)
    response = client.get("/query", params={"param": "value"})
    assert response.status_code == 422, response.text
    details = response.json()
    assert details["detail"][0]["input"] == {"param": "value"}