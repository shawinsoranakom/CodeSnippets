def test_swagger_ui_default_url():
    response = client.get("/docs")
    assert response.status_code == 404, response.text