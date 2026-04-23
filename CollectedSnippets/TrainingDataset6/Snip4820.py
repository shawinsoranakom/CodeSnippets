def test_get_openapi_json_default_url():
    response = client.get("/openapi.json")
    assert response.status_code == 404, response.text