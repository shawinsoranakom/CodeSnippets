def test_redoc_ui_default_url():
    response = client.get("/redoc")
    assert response.status_code == 404, response.text