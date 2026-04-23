def test_post_body(client: TestClient):
    data = [
        {"url": "http://example.com/", "name": "Example"},
        {"url": "http://fastapi.tiangolo.com/", "name": "FastAPI"},
    ]
    response = client.post("/images/multiple", json=data)
    assert response.status_code == 200, response.text
    assert response.json() == data