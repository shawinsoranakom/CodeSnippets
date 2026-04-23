def test_stream_session():
    response = client.get("/stream-session")
    assert response.text == "foobarbaz"