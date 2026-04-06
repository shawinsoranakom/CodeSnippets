def test_post_data_in_out(client: TestClient):
    response = client.post(
        "/data-in-out",
        json={
            "description": "A plumbus",
            "data": "SGVsbG8sIFdvcmxkIQ==",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "description": "A plumbus",
        "data": "SGVsbG8sIFdvcmxkIQ==",
    }