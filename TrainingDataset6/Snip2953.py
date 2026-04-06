def test_optional_bytes_list_no_files():
    client = TestClient(app)
    response = client.post("/files")
    assert response.status_code == 200
    assert response.json() == {"files_count": 0}