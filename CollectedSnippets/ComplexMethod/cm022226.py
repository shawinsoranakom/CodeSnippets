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
    run1_entry = _create_mock_entity("sensor", "initial")
    run2_entry = _create_mock_entity("sensor", "changed")
    assert run1_entry.device_id != run2_entry.device_id

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entity_id": "sensor.initial",
            "hysteresis": 0.0,
            "lower": -2.0,
            "name": "My threshold",
            "upper": None,
        },
        title="My threshold",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.entry_id not in _get_device_config_entries(run1_entry)
    assert config_entry.entry_id not in _get_device_config_entries(run2_entry)
    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    assert threshold_entity_entry.device_id == run1_entry.device_id

    hass.config_entries.async_update_entry(
        config_entry, options={**config_entry.options, "entity_id": "sensor.changed"}
    )
    hass.config_entries.async_schedule_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that the device association has updated
    assert config_entry.entry_id not in _get_device_config_entries(run1_entry)
    assert config_entry.entry_id not in _get_device_config_entries(run2_entry)
    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    assert threshold_entity_entry.device_id == run2_entry.device_id