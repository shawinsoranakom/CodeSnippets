def test_broken_session_stream_no_raise():
    """
    When a dependency with yield raises after the streaming response already started
    the 200 status code is already sent, but there's still an error in the server
    afterwards, an exception is raised and captured or shown in the server logs.
    """
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/broken-session-stream")
        assert response.status_code == 200
        assert response.text == ""