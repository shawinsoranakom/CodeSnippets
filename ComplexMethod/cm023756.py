async def test_intent(hass: HomeAssistant, init_wyoming_intent: ConfigEntry) -> None:
    """Test when an intent is recognized."""
    agent_id = "conversation.test_intent"
    conversation_id = "conversation-1234"
    satellite_id = "satellite-1234"
    device_id = "device-1234"

    test_intent = Intent(
        name="TestIntent",
        entities=[Entity(name="entity", value="value")],
        text="success",
    )

    class TestIntentHandler(intent.IntentHandler):
        """Test Intent Handler."""

        intent_type = "TestIntent"

        async def async_handle(self, intent_obj: intent.Intent):
            """Handle the intent."""
            assert intent_obj.slots.get("entity", {}).get("value") == "value"
            assert intent_obj.satellite_id == satellite_id
            assert intent_obj.device_id == device_id
            return intent_obj.create_response()

    intent.async_register(hass, TestIntentHandler())

    client = MockAsyncTcpClient([test_intent.event()])
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
            device_id=device_id,
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