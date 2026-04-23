async def test_wan_monitor_latency(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_websocket_message: WebsocketMessageMock,
    device_payload: list[dict[str, Any]],
    monitor_id: str,
    state: str,
    updated_state: str,
    index_to_update: int,
) -> None:
    """Verify that wan latency sensors are working as expected."""
    entity_id = f"sensor.mock_name_{monitor_id}_latency"

    assert len(hass.states.async_all()) == 6
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 2

    latency_entry = entity_registry.async_get(entity_id)
    assert latency_entry.disabled_by == RegistryEntryDisabler.INTEGRATION

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

    # Verify state update
    device = device_payload[0]
    device["uptime_stats"]["WAN"]["monitors"][index_to_update]["latency_average"] = (
        updated_state
    )

    mock_websocket_message(message=MessageKey.DEVICE, data=device)

    assert hass.states.get(entity_id).state == updated_state