async def test_intent_errors(hass: HomeAssistant) -> None:
    """Test the error conditions for set humidity and set mode intents."""
    assert await async_setup_component(hass, "homeassistant", {})
    entity_id = "humidifier.bedroom_humidifier"
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_HUMIDITY: 40,
            ATTR_SUPPORTED_FEATURES: 1,
            ATTR_AVAILABLE_MODES: ["home", "away"],
            ATTR_MODE: None,
        },
    )
    async_mock_service(hass, DOMAIN, SERVICE_SET_HUMIDITY)
    async_mock_service(hass, DOMAIN, SERVICE_SET_MODE)
    await intent.async_setup_intents(hass)

    # Humidifiers are exposed by default
    result = await async_handle(
        hass,
        "test",
        intent.INTENT_HUMIDITY,
        {"name": {"value": "Bedroom humidifier"}, "humidity": {"value": "50"}},
        assistant=conversation.DOMAIN,
    )
    assert result.response_type == IntentResponseType.ACTION_DONE

    result = await async_handle(
        hass,
        "test",
        intent.INTENT_MODE,
        {"name": {"value": "Bedroom humidifier"}, "mode": {"value": "away"}},
        assistant=conversation.DOMAIN,
    )
    assert result.response_type == IntentResponseType.ACTION_DONE

    # Unexposing it should fail
    async_expose_entity(hass, conversation.DOMAIN, entity_id, False)

    with pytest.raises(MatchFailedError) as err:
        await async_handle(
            hass,
            "test",
            intent.INTENT_HUMIDITY,
            {"name": {"value": "Bedroom humidifier"}, "humidity": {"value": "50"}},
            assistant=conversation.DOMAIN,
        )
    assert err.value.result.no_match_reason == MatchFailedReason.ASSISTANT

    with pytest.raises(MatchFailedError) as err:
        await async_handle(
            hass,
            "test",
            intent.INTENT_MODE,
            {"name": {"value": "Bedroom humidifier"}, "mode": {"value": "away"}},
            assistant=conversation.DOMAIN,
        )
    assert err.value.result.no_match_reason == MatchFailedReason.ASSISTANT

    # Expose again to test other errors
    async_expose_entity(hass, conversation.DOMAIN, entity_id, True)

    # Empty name should fail
    with pytest.raises(InvalidSlotInfo):
        await async_handle(
            hass,
            "test",
            intent.INTENT_HUMIDITY,
            {"name": {"value": ""}, "humidity": {"value": "50"}},
            assistant=conversation.DOMAIN,
        )

    with pytest.raises(InvalidSlotInfo):
        await async_handle(
            hass,
            "test",
            intent.INTENT_MODE,
            {"name": {"value": ""}, "mode": {"value": "away"}},
            assistant=conversation.DOMAIN,
        )

    # Wrong name should fail
    with pytest.raises(MatchFailedError) as err:
        await async_handle(
            hass,
            "test",
            intent.INTENT_HUMIDITY,
            {"name": {"value": "does not exist"}, "humidity": {"value": "50"}},
            assistant=conversation.DOMAIN,
        )
    assert err.value.result.no_match_reason == MatchFailedReason.NAME

    with pytest.raises(MatchFailedError) as err:
        await async_handle(
            hass,
            "test",
            intent.INTENT_MODE,
            {"name": {"value": "does not exist"}, "mode": {"value": "away"}},
            assistant=conversation.DOMAIN,
        )
    assert err.value.result.no_match_reason == MatchFailedReason.NAME