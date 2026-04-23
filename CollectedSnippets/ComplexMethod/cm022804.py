async def test_migrate(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    target_domain: Platform,
) -> None:
    """Test migration."""
    # Switch config entry, device and entity
    switch_config_entry = MockConfigEntry()
    switch_config_entry.add_to_hass(hass)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=switch_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    switch_entity_entry = entity_registry.async_get_or_create(
        "switch",
        "test",
        "unique",
        config_entry=switch_config_entry,
        device_id=device_entry.id,
        original_name="ABC",
        suggested_object_id="test",
    )
    assert switch_entity_entry.entity_id == "switch.test"

    # Switch_as_x config entry, device and entity
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: "switch.test",
            CONF_TARGET_DOMAIN: target_domain,
        },
        title="ABC",
        version=1,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)
    device_registry.async_update_device(
        device_entry.id, add_config_entry_id=config_entry.entry_id
    )
    switch_as_x_entity_entry = entity_registry.async_get_or_create(
        target_domain,
        "switch_as_x",
        config_entry.entry_id,
        capabilities=CAPABILITY_MAP[target_domain],
        config_entry=config_entry,
        device_id=device_entry.id,
        object_id_base="ABC",
        original_name="ABC",
        supported_features=SUPPORTED_FEATURE_MAP[target_domain],
    )
    entity_registry.async_update_entity_options(
        switch_as_x_entity_entry.entity_id,
        DOMAIN,
        {"entity_id": "switch.test", "invert": False},
    )

    events = track_entity_registry_actions(hass, switch_as_x_entity_entry.entity_id)

    # Setup the switch_as_x config entry
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert set(entity_registry.entities) == {
        switch_entity_entry.entity_id,
        switch_as_x_entity_entry.entity_id,
    }

    # Check migration was successful and added invert option
    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.options == {
        CONF_ENTITY_ID: "switch.test",
        CONF_INVERT: False,
        CONF_TARGET_DOMAIN: target_domain,
    }
    assert config_entry.version == SwitchAsXConfigFlowHandler.VERSION
    assert config_entry.minor_version == SwitchAsXConfigFlowHandler.MINOR_VERSION

    # Check the state and entity registry entry are present
    assert hass.states.get(f"{target_domain}.abc") is not None
    assert entity_registry.async_get(f"{target_domain}.abc") is not None

    # Entity removed from device to prevent deletion, then added back to device
    assert events == [
        {
            "action": "update",
            "changes": {"device_id": device_entry.id},
            "entity_id": switch_as_x_entity_entry.entity_id,
        },
        {
            "action": "update",
            "changes": {"device_id": None},
            "entity_id": switch_as_x_entity_entry.entity_id,
        },
    ]