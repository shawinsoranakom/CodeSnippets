def test_stream_simple():
    response = client.get("/stream-simple")
    assert response.text == "xyz"