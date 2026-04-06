def test_broken_session_stream_raise():
    # Can raise ValueError on Pydantic v2 and ExceptionGroup on Pydantic v1
    with pytest.raises((ValueError, Exception)):
        client.get("/broken-session-stream")