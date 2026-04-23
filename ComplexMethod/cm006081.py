def test_result_data_response_outputs(outputs_dict):
    """Test that ResultDataResponse properly handles and truncates outputs."""
    # Create OutputValue objects with potentially long messages
    outputs = {key: OutputValue(type="text", message=value) for key, value in outputs_dict.items()}

    response = ResultDataResponse(outputs=outputs)
    serialized = serialize(response, max_length=TEST_TEXT_LENGTH)

    # Check outputs are properly serialized and truncated
    for key, value in outputs_dict.items():
        assert key in serialized["outputs"]
        serialized_output = serialized["outputs"][key]
        assert serialized_output["type"] == "text"

        # Check message truncation
        message = serialized_output["message"]
        assert len(message) <= TEST_TEXT_LENGTH + len("..."), f"Message length: {len(message)}"
        if len(value) > TEST_TEXT_LENGTH:
            assert "..." in message
            assert message.startswith(value[:TEST_TEXT_LENGTH])
        else:
            assert message == value