def test_server_sent_event_null_id_rejected():
    with pytest.raises(ValueError, match="null"):
        ServerSentEvent(data="test", id="has\0null")