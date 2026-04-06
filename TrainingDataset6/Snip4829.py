def test_response_headers():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert "X-Process-Time" in response.headers