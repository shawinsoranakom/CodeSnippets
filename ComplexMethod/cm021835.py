async def test_account_sensors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    electrickiwi_api: AsyncMock,
    ek_auth: AsyncMock,
    entity_registry: EntityRegistry,
    sensor: str,
    sensor_state: str,
    device_class: str,
    state_class: str,
) -> None:
    """Test Account sensors for the Electric Kiwi integration."""

    await init_integration(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED

    entity = entity_registry.async_get(sensor)
    assert entity

    state = hass.states.get(sensor)
    assert state
    assert state.state == sensor_state
    assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
    assert state.attributes.get(ATTR_DEVICE_CLASS) == device_class
    assert state.attributes.get(ATTR_STATE_CLASS) == state_class