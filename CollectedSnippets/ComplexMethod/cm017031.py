def test_stream_chat(client: TestClient):
    response = client.post(
        "/chat/stream",
        json={"text": "hello world"},
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    lines = response.text.strip().split("\n")

    event_lines = [line for line in lines if line.startswith("event: ")]
    assert event_lines == [
        "event: token",
        "event: token",
        "event: done",
    ]

    data_lines = [line for line in lines if line.startswith("data: ")]
    assert data_lines == [
        'data: "hello"',
        'data: "world"',
        "data: [DONE]",
    ]