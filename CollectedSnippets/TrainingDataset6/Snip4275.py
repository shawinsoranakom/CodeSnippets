def test_server_sent_event_float_retry_rejected():
    with pytest.raises(ValueError):
        ServerSentEvent(data="test", retry=1.5)