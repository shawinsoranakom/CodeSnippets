async def test_custom_name_1(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    target_domain: Platform,
) -> None:
    """Test the source entity has a custom name."""
    switch_config_entry = MockConfigEntry()
    switch_config_entry.add_to_hass(hass)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=switch_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        name="Device name",
    )

    switch_entity_entry = entity_registry.async_get_or_create(
        "switch",
        "test",
        "unique",
        device_id=device_entry.id,
        has_entity_name=True,
        original_name="Original entity name",
    )
    switch_entity_entry = entity_registry.async_update_entity(
        switch_entity_entry.entity_id,
        config_entry_id=switch_config_entry.entry_id,
        name="Custom entity name",
    )

    # Add the config entry
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

    entity_entry = entity_registry.async_get(
        f"{target_domain}.device_name_original_entity_name"
    )
    assert entity_entry
    assert entity_entry.device_id == switch_entity_entry.device_id
    assert entity_entry.has_entity_name is True
    assert entity_entry.name == "Custom entity name"
    assert entity_entry.original_name == "Original entity name"
    assert entity_entry.options == {
        DOMAIN: {"entity_id": switch_entity_entry.entity_id, "invert": False}
    }