def test_static_files(client: TestClient):
    response = client.get("/static/sample.txt")
    assert response.status_code == 200, response.text
    assert response.text == "This is a sample static file."