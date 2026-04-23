async def test_trigger_sentences(hass: HomeAssistant) -> None:
    """Test registering/unregistering/matching a few trigger sentences."""
    trigger_sentences = ["It's party time", "It is time to party"]
    trigger_response = "Cowabunga!"

    manager = get_agent_manager(hass)

    callback = AsyncMock(return_value=trigger_response)
    unregister = manager.register_trigger(trigger_sentences, callback)

    result = await conversation.async_converse(hass, "Not the trigger", None, Context())
    assert result.response.response_type == intent.IntentResponseType.ERROR

    # Using different case and including punctuation
    test_sentences = ["it's party time!", "IT IS TIME TO PARTY."]
    for sentence in test_sentences:
        callback.reset_mock()
        result = await conversation.async_converse(hass, sentence, None, Context())
        assert callback.call_count == 1
        assert callback.call_args[0][0].text == sentence
        assert result.response.response_type == intent.IntentResponseType.ACTION_DONE, (
            sentence
        )
        assert result.response.speech == {
            "plain": {"speech": trigger_response, "extra_data": None}
        }

    unregister()

    # Should produce errors now
    callback.reset_mock()
    for sentence in test_sentences:
        result = await conversation.async_converse(hass, sentence, None, Context())
        assert result.response.response_type == intent.IntentResponseType.ERROR, (
            sentence
        )

    assert len(callback.mock_calls) == 0