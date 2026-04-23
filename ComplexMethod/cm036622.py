def test_basic_publishing(publisher, subscriber):
    """Test basic event publishing works"""

    test_batch = create_test_events(5)
    publisher.publish(test_batch)

    result = subscriber.receive_one(timeout=1000)
    assert result is not None, "No message received"

    seq, received = result
    assert seq == 0, "Sequence number mismatch"
    assert received.ts == pytest.approx(test_batch.ts, abs=0.1), "Timestamp mismatch"
    assert len(received.events) == len(test_batch.events), "Number of events mismatch"

    for i, event in enumerate(received.events):
        assert event.id == i, "Event id mismatch"
        assert event.value == f"test-{i}", "Event value mismatch"