def test_stream_items(client: TestClient):
    response = client.get("/items/stream")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    lines = response.text.strip().split("\n")

    # First event is a comment-only event
    assert lines[0] == ": stream of item updates"

    # Remaining lines contain event:, data:, id:, retry: fields
    event_lines = [line for line in lines if line.startswith("event: ")]
    assert len(event_lines) == 3
    assert all(line == "event: item_update" for line in event_lines)

    data_lines = [line for line in lines if line.startswith("data: ")]
    assert len(data_lines) == 3

    id_lines = [line for line in lines if line.startswith("id: ")]
    assert id_lines == ["id: 1", "id: 2", "id: 3"]

    retry_lines = [line for line in lines if line.startswith("retry: ")]
    assert len(retry_lines) == 3
    assert all(line == "retry: 5000" for line in retry_lines)