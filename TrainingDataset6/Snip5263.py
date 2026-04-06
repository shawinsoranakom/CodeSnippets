def test_stream_logs(client: TestClient):
    response = client.get("/logs/stream")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    data_lines = [
        line for line in response.text.strip().split("\n") if line.startswith("data: ")
    ]
    assert len(data_lines) == 3

    # raw_data is sent without JSON encoding (no quotes around the string)
    assert data_lines[0] == "data: 2025-01-01 INFO  Application started"
    assert data_lines[1] == "data: 2025-01-01 DEBUG Connected to database"
    assert data_lines[2] == "data: 2025-01-01 WARN  High memory usage detected"