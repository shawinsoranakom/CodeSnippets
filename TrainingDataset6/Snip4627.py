def test_get_custom_response(client: TestClient):
    response = client.get("/items/")
    assert response.status_code == 200, response.text
    assert response.text == html_contents