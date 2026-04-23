def test_request_class(client: TestClient):
    response = client.get("/check-class")
    assert response.json() == {"request_class": "GzipRequest"}