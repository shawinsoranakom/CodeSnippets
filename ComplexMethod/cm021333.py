async def old_entity_and_device_removal(
    hass: HomeAssistant, mock_mqtt, platform, entity_config, value_key, index
):
    """Test that old entities are correctly identified and removed across different platforms."""

    set_mock_mqtt(
        mock_mqtt,
        config=entity_config,
        status_value=entity_config[value_key],
        gw_available=True,
        device_available=True,
    )

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        title="iNELS",
    )
    config_entry.add_to_hass(hass)

    # Create an old entity
    entity_registry = er.async_get(hass)
    old_entity = entity_registry.async_get_or_create(
        domain=platform,
        platform=DOMAIN,
        unique_id=f"old_{entity_config['unique_id']}",
        suggested_object_id=f"old_inels_{platform}_{entity_config['device_type']}",
        config_entry=config_entry,
    )

    # Create a device and associate it with the old entity
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, f"old_{entity_config['unique_id']}")},
        name=f"iNELS {platform.capitalize()} {entity_config['device_type']}",
        manufacturer="iNELS",
        model=entity_config["device_type"],
    )

    # Associate the old entity with the device
    entity_registry.async_update_entity(old_entity.entity_id, device_id=device.id)

    assert (
        device_registry.async_get_device({(DOMAIN, old_entity.unique_id)}) is not None
    )

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # The device was discovered, and at this point, the async_remove_old_entities function was called
    assert config_entry.runtime_data.devices
    assert old_entity.entity_id not in config_entry.runtime_data.old_entities[platform]

    # Get the new entity
    new_entity = entity_registry.async_get(get_entity_id(entity_config, index).lower())

    assert new_entity is not None

    # Verify that the new entity is in the registry
    assert entity_registry.async_get(new_entity.entity_id) is not None

    # Verify that the old entity is no longer in the registry
    assert entity_registry.async_get(old_entity.entity_id) is None

    # Verify that the device no longer exists in the registry
    assert device_registry.async_get_device({(DOMAIN, old_entity.unique_id)}) is None