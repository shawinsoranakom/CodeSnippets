async def test_handle(hass: HomeAssistant, init_wyoming_handle: ConfigEntry) -> None:
    """Test when an intent is handled."""
    agent_id = "conversation.test_handle"
    conversation_id = "conversation-1234"
    satellite_id = "satellite-1234"

    client = MockAsyncTcpClient([Handled(text="success").event()])
    with patch(
        "homeassistant.components.wyoming.conversation.AsyncTcpClient",
        client,
    ):
        result = await conversation.async_converse(
            hass=hass,
            text="test text",
            conversation_id=conversation_id,
            context=Context(),
            language=hass.config.language,
            agent_id=agent_id,
            satellite_id=satellite_id,
        )

    # Ensure language and context are sent
    assert client.transcript is not None
    assert client.transcript.language == hass.config.language
    assert client.transcript.context == {
        "conversation_id": conversation_id,
        "satellite_id": satellite_id,
    }

    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
    assert result.response.speech, "No speech"
    assert result.response.speech.get("plain", {}).get("speech") == "success"
    assert result.conversation_id == conversation_id