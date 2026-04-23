async def test_exception_run_with_callbacks(mock_dependencies):
    instance = TestClassWithCallbacks()

    event_manager = mock_dependencies["event_manager"]

    # The decorator now re-raises the exception after logging and encoding the error event
    with pytest.raises(ValueError):  # noqa: PT011
        await instance.run_exception(event_manager=event_manager, data="fail_data")

    # 1. Assert error was logged
    mock_dependencies["logger"].aerror.assert_called_once()
    mock_dependencies["logger"].aerror.assert_called_with("Exception in TestClassWithCallbacks: ")

    # 2. Assert encoder was called twice (once for BEFORE event, once for ERROR event)
    assert mock_dependencies["encoder"].encode.call_count == 2

    # 3. Verify the encoder was called with the correct payloads
    encoder_instance = mock_dependencies["encoder"]
    assert encoder_instance.encode.call_count == 2

    # Get the actual calls to encode
    encode_calls = encoder_instance.encode.call_args_list

    # First call should be the BEFORE event (StepStartedEvent)
    before_event = encode_calls[0][0][0]
    assert isinstance(before_event, StepStartedEvent)
    assert before_event.raw_event["lifecycle"] == "start"

    # Second call should be the ERROR event (CustomEvent)
    error_event = encode_calls[1][0][0]
    assert isinstance(error_event, CustomEvent)
    assert error_event.name == "error"
    assert error_event.value["error"] == ""
    assert error_event.value["error_type"] == "ValueError"
    assert error_event.raw_event["lifecycle"] == "error"

    # 4. Assert no warnings were logged
    mock_dependencies["logger"].awarning.assert_not_called()