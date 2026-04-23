async def test_device_temperatures(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_websocket_message,
    device_payload: list[dict[str, Any]],
    temperature_id: str,
    state: str,
    updated_state: str,
    index_to_update: int,
) -> None:
    """Verify that device temperatures sensors are working as expected."""

    entity_id = f"sensor.device_{temperature_id}_temperature"

    assert len(hass.states.async_all()) == 6
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 2

    temperature_entity = entity_registry.async_get(entity_id)
    assert temperature_entity.disabled_by == RegistryEntryDisabler.INTEGRATION

    # Enable entity
    entity_registry.async_update_entity(entity_id=entity_id, disabled_by=None)

    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 7
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 3

    # Verify sensor state
    assert hass.states.get(entity_id).state == state

    # # Verify state update
    device = device_payload[0]
    device["temperatures"][index_to_update]["value"] = updated_state

    mock_websocket_message(message=MessageKey.DEVICE, data=device)

    assert hass.states.get(entity_id).state == updated_state