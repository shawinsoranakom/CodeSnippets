def test_mixed_plain_and_sse_events(client: TestClient):
    response = client.get("/items/stream-mixed")
    assert response.status_code == 200
    text = response.text

    assert "event: special\n" in text
    assert 'data: "custom-event"\n' in text
    assert '"name"' in text