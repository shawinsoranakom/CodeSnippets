def test_static_files_not_found(client: TestClient):
    response = client.get("/static/non_existent_file.txt")
    assert response.status_code == 404, response.text