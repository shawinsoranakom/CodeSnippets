async def test_successful_run_with_callbacks(mock_dependencies):
    instance = TestClassWithCallbacks()
    data = "test_data"

    event_manager = mock_dependencies["event_manager"]

    result = await instance.run_success(event_manager=event_manager, data=data)

    # 1. Assert result
    assert result == f"Processed:{data}"

    # 2. Assert encoder was called twice (once for BEFORE, once for AFTER)
    assert mock_dependencies["encoder"].encode.call_count == 2

    # 3. Verify the encoder was called with the correct payloads
    encoder_instance = mock_dependencies["encoder"]
    assert encoder_instance.encode.call_count == 2

    # Get the actual calls to encode
    encode_calls = encoder_instance.encode.call_args_list

    # First call should be the BEFORE event (StepStartedEvent)
    before_event = encode_calls[0][0][0]
    assert isinstance(before_event, StepStartedEvent)
    assert before_event.step_name == "ObservableTest"
    assert before_event.raw_event["lifecycle"] == "start"
    assert before_event.raw_event["args_len"] == 0
    assert "event_manager" in before_event.raw_event["kw_keys"]
    assert "data" in before_event.raw_event["kw_keys"]

    # Second call should be the AFTER event (StepFinishedEvent)
    after_event = encode_calls[1][0][0]
    assert isinstance(after_event, StepFinishedEvent)
    assert after_event.step_name == "ObservableTest"
    assert after_event.raw_event["lifecycle"] == "end"
    assert after_event.raw_event["result"] == f"Processed:{data}"
    assert "event_manager" in after_event.raw_event["kw_keys"]
    assert "data" in after_event.raw_event["kw_keys"]

    # 4. Assert no warnings or errors were logged
    mock_dependencies["logger"].awarning.assert_not_called()
    mock_dependencies["logger"].aerror.assert_not_called()