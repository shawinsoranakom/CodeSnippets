async def test_device_registry_config_entry_3(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    target_domain: str,
) -> None:
    """Test we add our config entry to the tracked switch's device."""
    switch_config_entry = MockConfigEntry()
    switch_config_entry.add_to_hass(hass)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=switch_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    device_entry_2 = device_registry.async_get_or_create(
        config_entry_id=switch_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:FF")},
    )
    switch_entity_entry = entity_registry.async_get_or_create(
        "switch",
        "test",
        "unique",
        config_entry=switch_config_entry,
        device_id=device_entry.id,
        original_name="ABC",
    )

    switch_as_x_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: switch_entity_entry.id,
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        },
        title="ABC",
        version=SwitchAsXConfigFlowHandler.VERSION,
        minor_version=SwitchAsXConfigFlowHandler.MINOR_VERSION,
    )

    switch_as_x_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(switch_as_x_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_entry = entity_registry.async_get(f"{target_domain}.abc")
    assert entity_entry.device_id == switch_entity_entry.device_id

    device_entry = device_registry.async_get(device_entry.id)
    assert switch_as_x_config_entry.entry_id not in device_entry.config_entries
    device_entry_2 = device_registry.async_get(device_entry_2.id)
    assert switch_as_x_config_entry.entry_id not in device_entry_2.config_entries

    events = []

    def add_event(event: Event[er.EventEntityRegistryUpdatedData]) -> None:
        """Add entity registry updated event to the list."""
        events.append(event.data["action"])

    async_track_entity_registry_updated_event(hass, entity_entry.entity_id, add_event)

    # Move the wrapped switch to another device
    with patch(
        "homeassistant.components.switch_as_x.async_unload_entry",
        wraps=switch_as_x.async_unload_entry,
    ) as mock_setup_entry:
        entity_registry.async_update_entity(
            switch_entity_entry.entity_id, device_id=device_entry_2.id
        )
        await hass.async_block_till_done()
    mock_setup_entry.assert_called_once()

    # Check that the switch_as_x config entry is moved to the other device
    device_entry = device_registry.async_get(device_entry.id)
    assert switch_as_x_config_entry.entry_id not in device_entry.config_entries
    device_entry_2 = device_registry.async_get(device_entry_2.id)
    assert switch_as_x_config_entry.entry_id not in device_entry_2.config_entries

    # Check that the switch_as_x config entry is not removed
    assert switch_as_x_config_entry.entry_id in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    assert events == ["update"]