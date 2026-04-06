def test_optional_bytes_list():
    client = TestClient(app)
    response = client.post(
        "/files",
        files=[("files", b"content1"), ("files", b"content2")],
    )
    assert response.status_code == 200
    assert response.json() == {"files_count": 2, "sizes": [8, 8]}