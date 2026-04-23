async def test_enabling_disable_by_default(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    mock_forecast_solar: MagicMock,
    key: str,
    name: str,
    value: str,
) -> None:
    """Test the Forecast.Solar sensors that are disabled by default."""
    entry_id = mock_config_entry.entry_id
    entity_id = f"{SENSOR_DOMAIN}.{key}"

    # Pre-create registry entry for disabled by default sensor
    entity_registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        f"{entry_id}_{key}",
        suggested_object_id=key,
        disabled_by=None,
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    entry = entity_registry.async_get(entity_id)
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_{key}"
    assert state.state == value
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME) == f"Solar production forecast {name}"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) is None
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.WATT
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.POWER
    assert ATTR_ICON not in state.attributes