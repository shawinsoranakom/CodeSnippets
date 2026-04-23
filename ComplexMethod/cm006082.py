def test_result_data_response_logs(log_messages):
    """Test that ResultDataResponse properly handles and truncates logs."""
    # Create logs with long messages
    logs = {
        "test_node": [
            Log(
                message=msg,
                name="test_log",
                type="test",
            )
            for msg in log_messages
        ]
    }

    response = ResultDataResponse(logs=logs)
    serialized = serialize(response, max_length=TEST_TEXT_LENGTH)

    # Check logs are properly serialized and truncated
    assert "test_node" in serialized["logs"]
    serialized_logs = serialized["logs"]["test_node"]

    for i, log_msg in enumerate(log_messages):
        serialized_log = serialized_logs[i]
        assert serialized_log["name"] == "test_log"
        assert serialized_log["type"] == "test"

        # Check message truncation
        message = serialized_log["message"]
        assert len(message) <= TEST_TEXT_LENGTH + len("...")
        if len(log_msg) > TEST_TEXT_LENGTH:
            assert "..." in message
            assert message.startswith(log_msg[:TEST_TEXT_LENGTH])
        else:
            assert message == log_msg