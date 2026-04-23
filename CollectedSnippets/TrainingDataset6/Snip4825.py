def test_swagger_ui_custom_url():
    response = client.get("/documentation")
    assert response.status_code == 200, response.text
    assert "<title>FastAPI - Swagger UI</title>" in response.text