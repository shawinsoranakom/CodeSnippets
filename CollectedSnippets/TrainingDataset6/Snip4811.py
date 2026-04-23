def test_post_data(client: TestClient):
    response = client.post(
        "/data",
        json={
            "description": "A file",
            "data": "SGVsbG8sIFdvcmxkIQ==",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"description": "A file", "content": "Hello, World!"}