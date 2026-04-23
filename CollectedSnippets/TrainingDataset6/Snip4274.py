def test_server_sent_event_negative_retry_rejected():
    with pytest.raises(ValueError):
        ServerSentEvent(data="test", retry=-1)