def test_stream_bare_async_iterable():
    response = client.get("/items/stream-bare-async")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/jsonl"
    lines = [json.loads(line) for line in response.text.strip().splitlines()]
    assert lines == [{"name": "foo"}]