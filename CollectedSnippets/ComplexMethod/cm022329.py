async def test_enable_sensor(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_bridge_v2: Mock,
    v2_resources_test_data: JsonArrayType,
    mock_config_entry_v2: MockConfigEntry,
) -> None:
    """Test enabling of the by default disabled zigbee_connectivity sensor."""
    await mock_bridge_v2.api.load_test_data(v2_resources_test_data)
    await setup_bridge(hass, mock_bridge_v2, mock_config_entry_v2)

    assert await async_setup_component(hass, hue.DOMAIN, {}) is True
    await hass.async_block_till_done()
    await hass.config_entries.async_forward_entry_setups(
        mock_config_entry_v2, [Platform.SENSOR]
    )

    entity_id = "sensor.wall_switch_with_2_controls_zigbee_connectivity"
    entity_entry = entity_registry.async_get(entity_id)

    assert entity_entry
    assert entity_entry.disabled
    assert entity_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    # enable the entity
    updated_entry = entity_registry.async_update_entity(
        entity_entry.entity_id, disabled_by=None
    )
    assert updated_entry != entity_entry
    assert updated_entry.disabled is False

    # reload platform and check if entity is correctly there
    await hass.config_entries.async_forward_entry_unload(
        mock_config_entry_v2, Platform.SENSOR
    )
    await hass.config_entries.async_forward_entry_setups(
        mock_config_entry_v2, [Platform.SENSOR]
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "connected"
    assert state.attributes["mac_address"] == "00:17:88:01:0b:aa:bb:99"