async def test_vacuum(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mocked_vacuum: Device,
) -> None:
    """Test initialization."""
    await setup_platform_for_device(
        hass, mock_config_entry, Platform.VACUUM, mocked_vacuum
    )

    device_entries = dr.async_entries_for_config_entry(
        device_registry, mock_config_entry.entry_id
    )
    assert device_entries

    entity = entity_registry.async_get(ENTITY_ID)
    assert entity
    assert entity.unique_id == f"{DEVICE_ID}-vacuum"

    state = hass.states.get(ENTITY_ID)
    assert state.state == VacuumActivity.DOCKED

    assert state.attributes[ATTR_FAN_SPEED] == "max"
    assert state.attributes[ATTR_BATTERY_LEVEL] == 100
    result = translation.async_translate_state(
        hass, "max", "vacuum", "tplink", "vacuum.state_attributes.fan_speed", None
    )
    assert result == "Max"