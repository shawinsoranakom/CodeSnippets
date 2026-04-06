def test_raw_data_sent_without_json_encoding(client: TestClient):
    """raw_data is sent as-is, not JSON-encoded."""
    response = client.get("/items/stream-raw")
    assert response.status_code == 200
    text = response.text

    # raw_data should appear without JSON quotes
    assert "data: plain text without quotes\n" in text
    # Not JSON-quoted
    assert 'data: "plain text without quotes"' not in text

    assert "event: html\n" in text
    assert "data: <div>html fragment</div>\n" in text

    assert "event: csv\n" in text
    assert "data: cpu,87.3,1709145600\n" in text