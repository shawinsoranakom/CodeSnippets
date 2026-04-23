def test_result_data_response_combined_fields(outputs_dict, log_messages):
    """Test that ResultDataResponse properly handles all fields together."""
    # Create OutputValue objects with potentially long messages
    outputs = {key: OutputValue(type="text", message=value) for key, value in outputs_dict.items()}

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

    response = ResultDataResponse(
        outputs=outputs,
        logs=logs,
        results={"test": "value"},
        message={"text": "test"},
        artifacts={"file": "test.txt"},
    )
    serialized = serialize(response, max_length=TEST_TEXT_LENGTH)

    # Check all fields are present
    assert "outputs" in serialized
    assert "logs" in serialized
    assert "results" in serialized
    assert "message" in serialized
    assert "artifacts" in serialized

    # Check outputs truncation
    for key, value in outputs_dict.items():
        assert key in serialized["outputs"]
        serialized_output = serialized["outputs"][key]
        assert serialized_output["type"] == "text"

        # Check message truncation
        message = serialized_output["message"]
        if len(value) > TEST_TEXT_LENGTH:
            assert len(message) <= TEST_TEXT_LENGTH + len("...")
            assert "..." in message
        else:
            assert message == value

    # Check logs truncation
    assert "test_node" in serialized["logs"]
    serialized_logs = serialized["logs"]["test_node"]

    for i, log_msg in enumerate(log_messages):
        serialized_log = serialized_logs[i]
        assert serialized_log["name"] == "test_log"
        assert serialized_log["type"] == "test"

        # Check message truncation
        message = serialized_log["message"]
        if len(log_msg) > TEST_TEXT_LENGTH:
            assert len(message) <= TEST_TEXT_LENGTH + len("...")
            assert "..." in message
        else:
            assert message == log_msg