async def test_manual_pause_unpause(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test unpausing a media player that was manually paused outside of voice."""
    await media_player_intent.async_setup_intents(hass)

    attributes = {ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.PAUSE}

    # Create two playing devices
    device_1 = entity_registry.async_get_or_create("media_player", "test", "device-1")
    device_1 = entity_registry.async_update_entity(device_1.entity_id, name="device 1")
    hass.states.async_set(device_1.entity_id, STATE_PLAYING, attributes=attributes)

    device_2 = entity_registry.async_get_or_create("media_player", "test", "device-2")
    device_2 = entity_registry.async_update_entity(device_2.entity_id, name="device 2")
    hass.states.async_set(device_2.entity_id, STATE_PLAYING, attributes=attributes)

    # Pause both devices by voice
    context = Context()
    calls = async_mock_service(hass, DOMAIN, SERVICE_MEDIA_PAUSE)
    response = await intent.async_handle(
        hass,
        "test",
        media_player_intent.INTENT_MEDIA_PAUSE,
        context=context,
    )
    await hass.async_block_till_done()
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert len(calls) == 2

    hass.states.async_set(
        device_1.entity_id, STATE_PAUSED, attributes=attributes, context=context
    )
    hass.states.async_set(
        device_2.entity_id, STATE_PAUSED, attributes=attributes, context=context
    )

    # Unpause both devices by voice
    context = Context()
    calls = async_mock_service(hass, DOMAIN, SERVICE_MEDIA_PLAY)
    response = await intent.async_handle(
        hass,
        "test",
        media_player_intent.INTENT_MEDIA_UNPAUSE,
        context=context,
    )
    await hass.async_block_till_done()
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert len(calls) == 2

    hass.states.async_set(
        device_1.entity_id, STATE_PLAYING, attributes=attributes, context=context
    )
    hass.states.async_set(
        device_2.entity_id, STATE_PLAYING, attributes=attributes, context=context
    )

    # Pause the first device by voice
    context = Context()
    calls = async_mock_service(hass, DOMAIN, SERVICE_MEDIA_PAUSE)
    response = await intent.async_handle(
        hass,
        "test",
        media_player_intent.INTENT_MEDIA_PAUSE,
        {"name": {"value": "device 1"}},
        context=context,
    )
    await hass.async_block_till_done()
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert len(calls) == 1
    assert calls[0].data == {"entity_id": device_1.entity_id}

    hass.states.async_set(
        device_1.entity_id, STATE_PAUSED, attributes=attributes, context=context
    )

    # "Manually" pause the second device (outside of voice)
    context = Context()
    hass.states.async_set(
        device_2.entity_id, STATE_PAUSED, attributes=attributes, context=context
    )

    # Unpause with no constraints.
    # Should resume the more recently (manually) paused device.
    context = Context()
    calls = async_mock_service(hass, DOMAIN, SERVICE_MEDIA_PLAY)
    response = await intent.async_handle(
        hass,
        "test",
        media_player_intent.INTENT_MEDIA_UNPAUSE,
        context=context,
    )
    await hass.async_block_till_done()
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert len(calls) == 1
    assert calls[0].data == {"entity_id": device_2.entity_id}