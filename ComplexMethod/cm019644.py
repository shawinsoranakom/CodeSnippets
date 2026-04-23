async def test_entry_changed(hass: HomeAssistant, platform) -> None:
    """Test reconfiguring."""

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    def _create_mock_entity(domain: str, name: str) -> er.RegistryEntry:
        config_entry = MockConfigEntry(
            data={},
            domain="test",
            title=f"{name}",
        )
        config_entry.add_to_hass(hass)
        device_entry = device_registry.async_get_or_create(
            identifiers={("test", name)}, config_entry_id=config_entry.entry_id
        )
        return entity_registry.async_get_or_create(
            domain, "test", name, suggested_object_id=name, device_id=device_entry.id
        )

    def _get_device_config_entries(entry: er.RegistryEntry) -> set[str]:
        assert entry.device_id
        device = device_registry.async_get(entry.device_id)
        assert device
        return device.config_entries

    # Set up entities, with backing devices and config entries
    input_entry = _create_mock_entity("sensor", "input")
    valid_entry = _create_mock_entity("sensor", "valid")
    assert input_entry.device_id != valid_entry.device_id

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "method": "left",
            "name": "My integration",
            "source": "sensor.input",
            "unit_time": "min",
        },
        title="My integration",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.entry_id not in _get_device_config_entries(input_entry)
    assert config_entry.entry_id not in _get_device_config_entries(valid_entry)
    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    assert integration_entity_entry.device_id == input_entry.device_id

    hass.config_entries.async_update_entry(
        config_entry, options={**config_entry.options, "source": "sensor.valid"}
    )
    hass.config_entries.async_schedule_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that the device association has updated
    assert config_entry.entry_id not in _get_device_config_entries(input_entry)
    assert config_entry.entry_id not in _get_device_config_entries(valid_entry)
    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    assert integration_entity_entry.device_id == valid_entry.device_id