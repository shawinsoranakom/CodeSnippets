async def test_device_identifier_migration(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test being able to unload an entry."""
    original_identifiers = {(DOMAIN, "module_address", "module_serial")}
    target_identifiers = {(DOMAIN, "module_address")}

    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers=original_identifiers,  # type: ignore[arg-type]
        name="channel_name",
        manufacturer="Velleman",
        model="module_type_name",
        sw_version="module_sw_version",
    )
    assert device_registry.async_get_device(
        identifiers=original_identifiers  # type: ignore[arg-type]
    )
    assert not device_registry.async_get_device(identifiers=target_identifiers)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert not device_registry.async_get_device(
        identifiers=original_identifiers  # type: ignore[arg-type]
    )
    device_entry = device_registry.async_get_device(identifiers=target_identifiers)
    assert device_entry
    assert device_entry.name == "channel_name"
    assert device_entry.manufacturer == "Velleman"
    assert device_entry.model == "module_type_name"
    assert device_entry.sw_version == "module_sw_version"