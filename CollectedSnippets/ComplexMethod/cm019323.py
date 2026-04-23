async def test_remove_config_entry_device(
    hass: HomeAssistant,
    mock_envoy: AsyncMock,
    config_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test removing enphase_envoy config entry device."""
    assert await async_setup_component(hass, "config", {})
    await setup_integration(hass, config_entry)

    # use client to send remove_device command
    hass_client = await hass_ws_client(hass)

    # add device that will pass remove test
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "delete_this_device")},
    )
    response = await hass_client.remove_device(device_entry.id, config_entry.entry_id)
    assert response["success"]

    # inverters are not allowed to be removed
    entity = entity_registry.entities["sensor.inverter_1"]
    device_entry = device_registry.async_get(entity.device_id)
    response = await hass_client.remove_device(device_entry.id, config_entry.entry_id)
    assert not response["success"]

    # envoy itself is not allowed to be removed
    entity = entity_registry.entities["sensor.envoy_1234_current_power_production"]
    device_entry = device_registry.async_get(entity.device_id)
    response = await hass_client.remove_device(device_entry.id, config_entry.entry_id)
    assert not response["success"]

    # encharge can not be removed
    entity = entity_registry.entities["sensor.encharge_123456_power"]
    device_entry = device_registry.async_get(entity.device_id)
    response = await hass_client.remove_device(device_entry.id, config_entry.entry_id)
    assert not response["success"]

    # enpower can not be removed
    entity = entity_registry.entities["sensor.enpower_654321_temperature"]
    device_entry = device_registry.async_get(entity.device_id)
    response = await hass_client.remove_device(device_entry.id, config_entry.entry_id)
    assert not response["success"]

    # relays can be removed
    entity = entity_registry.entities["switch.nc1_fixture"]
    device_entry = device_registry.async_get(entity.device_id)
    response = await hass_client.remove_device(device_entry.id, config_entry.entry_id)
    assert response["success"]