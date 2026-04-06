def test_sync_generator_no_annotation(client: TestClient):
    response = client.get("/items/stream-sync-no-annotation")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    data_lines = [
        line for line in response.text.strip().split("\n") if line.startswith("data: ")
    ]
    assert len(data_lines) == 3