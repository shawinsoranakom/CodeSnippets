def test_stream_items(client: TestClient, path: str):
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/jsonl"
    lines = [json.loads(line) for line in response.text.strip().splitlines()]
    assert lines == expected_items