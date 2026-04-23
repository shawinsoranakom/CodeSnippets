async def test_broadcast_intent(
    hass: HomeAssistant,
    init_components: ConfigEntry,
    entity: MockAssistSatellite,
    entity2: MockAssistSatellite,
    entity_no_features: MockAssistSatellite,
    mock_tts: None,
) -> None:
    """Test we can invoke a broadcast intent."""

    with patch(
        "homeassistant.components.tts.async_resolve_engine",
        return_value="tts.cloud",
    ):
        result = await intent.async_handle(
            hass, "test", intent.INTENT_BROADCAST, {"message": {"value": "Hello"}}
        )

    assert result.as_dict() == {
        "card": {},
        "data": {
            "failed": [],
            "success": [
                {
                    "id": "assist_satellite.test_entity",
                    "name": "Test Entity",
                    "type": intent.IntentResponseTargetType.ENTITY,
                },
                {
                    "id": "assist_satellite.test_entity_2",
                    "name": "Test Entity 2",
                    "type": intent.IntentResponseTargetType.ENTITY,
                },
            ],
        },
        "language": "en",
        "response_type": "action_done",
        "speech": {},  # response comes from intents
    }
    assert len(entity.announcements) == 1
    assert len(entity2.announcements) == 1
    assert len(entity_no_features.announcements) == 0

    with patch(
        "homeassistant.components.tts.async_resolve_engine",
        return_value="tts.cloud",
    ):
        result = await intent.async_handle(
            hass,
            "test",
            intent.INTENT_BROADCAST,
            {"message": {"value": "Hello"}},
            device_id=entity.device_entry.id,
        )
    # Broadcast doesn't targets device that triggered it.
    assert result.as_dict() == {
        "card": {},
        "data": {
            "failed": [],
            "success": [
                {
                    "id": "assist_satellite.test_entity_2",
                    "name": "Test Entity 2",
                    "type": intent.IntentResponseTargetType.ENTITY,
                },
            ],
        },
        "language": "en",
        "response_type": "action_done",
        "speech": {},  # response comes from intents
    }
    assert len(entity.announcements) == 1
    assert len(entity2.announcements) == 2