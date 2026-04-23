def test_fast_detokenization_text_detection(
    parser_fixture, model_output, fake_count, two_phase, request
):
    """Regression: bot_token in text but not token_ids (PR #37209)."""
    parser = request.getfixturevalue(parser_fixture)
    # Token IDs that do NOT contain bot_token_id.
    fake_token_ids = list(range(99, 99 + fake_count))

    if two_phase:
        # First delta: pure content, no bot token yet
        delta_message_before = parser.extract_tool_calls_streaming(
            previous_text="",
            current_text="Hello",
            delta_text="Hello",
            previous_token_ids=[],
            current_token_ids=[99],
            delta_token_ids=[99],
            request=_DUMMY_REQUEST,
        )
        assert delta_message_before is not None
        assert delta_message_before.content == "Hello"
        assert not delta_message_before.tool_calls

        previous_text = "Hello"
        current_text = "Hello" + model_output
        previous_token_ids = [99]
        delta_token_ids = fake_token_ids[1:]
    else:
        previous_text = ""
        current_text = model_output
        previous_token_ids = []
        delta_token_ids = fake_token_ids

    delta_message = parser.extract_tool_calls_streaming(
        previous_text=previous_text,
        current_text=current_text,
        delta_text=model_output,
        previous_token_ids=previous_token_ids,
        current_token_ids=fake_token_ids,
        delta_token_ids=delta_token_ids,
        request=_DUMMY_REQUEST,
    )
    assert delta_message is not None
    assert delta_message.tool_calls is not None
    assert len(delta_message.tool_calls) == 1
    assert delta_message.tool_calls[0].function is not None
    assert delta_message.tool_calls[0].function.name == "add"