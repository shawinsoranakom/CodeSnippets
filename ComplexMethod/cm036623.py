def test_data_parallel_rank_tagging(publisher_config):
    """Test that events are properly tagged with their data parallel rank"""

    publisher_config.topic = "foo"
    pub_0 = EventPublisherFactory.create(publisher_config, DP_RANK)
    pub_1 = EventPublisherFactory.create(publisher_config, DP_RANK + 1)

    # Hardcode the expected endpoints based on port offsetting behavior
    # Both ranks get offsets according to _offset_endpoint_port function
    base_endpoint = publisher_config.endpoint
    if "tcp://" in base_endpoint:
        # For TCP endpoints: tcp://localhost:5557 -> tcp://localhost:5557, tcp://localhost:5558
        expected_endpoint_0 = base_endpoint  # rank 0 gets port + 0 = same port
        expected_endpoint_1 = base_endpoint.replace(
            ":5557", ":5558"
        )  # rank 1 gets port + 1
    else:
        # For inproc endpoints: inproc://test -> inproc://test_dp0, inproc://test_dp1
        expected_endpoint_0 = base_endpoint  # rank 0 gets base
        expected_endpoint_1 = base_endpoint + "_dp1"  # rank 1 gets _dp1

    from .conftest import MockSubscriber

    sub_0 = MockSubscriber(expected_endpoint_0, None, publisher_config.topic)
    sub_1 = MockSubscriber(expected_endpoint_1, None, publisher_config.topic)

    try:
        time.sleep(0.1)  # Let publishers start up

        # Publish events from different ranks
        batch_0 = create_test_events(2)
        batch_1 = create_test_events(3)

        pub_0.publish(batch_0)
        pub_1.publish(batch_1)

        # Receive events from rank 0
        result_0 = sub_0.receive_one(timeout=200)
        assert result_0 is not None, "No message received from rank 0"
        seq_0, received_0 = result_0

        # Receive events from rank 1
        result_1 = sub_1.receive_one(timeout=200)
        assert result_1 is not None, "No message received from rank 1"
        seq_1, received_1 = result_1

        # Verify DP rank tagging
        assert received_0.data_parallel_rank == 0, (
            f"Expected DP rank 0, got {received_0.data_parallel_rank}"
        )
        assert received_1.data_parallel_rank == 1, (
            f"Expected DP rank 1, got {received_1.data_parallel_rank}"
        )

        # Verify event content is correct
        assert len(received_0.events) == 2, "Wrong number of events from rank 0"
        assert len(received_1.events) == 3, "Wrong number of events from rank 1"

    finally:
        pub_0.shutdown()
        pub_1.shutdown()
        sub_0.close()
        sub_1.close()