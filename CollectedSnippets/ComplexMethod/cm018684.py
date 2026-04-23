async def test_basic(
    hass: HomeAssistant,
    mock_connection: MockConnection,
    model: Model,
    climate_id: str,
    entity_id: str,
    coils: dict[int, Any],
    snapshot: SnapshotAssertion,
) -> None:
    """Test setting of value."""
    climate, unit = _setup_climate_group(coils, model, climate_id)

    await async_add_model(hass, model)

    assert hass.states.get(entity_id) == snapshot(name="initial")

    mock_connection.mock_coil_update(unit.prio, "COOLING")
    assert hass.states.get(entity_id) == snapshot(name="cooling")

    mock_connection.mock_coil_update(unit.prio, "HEAT")
    assert hass.states.get(entity_id) == snapshot(name="heating")

    mock_connection.mock_coil_update(climate.mixing_valve_state, 30)
    assert hass.states.get(entity_id) == snapshot(name="idle (mixing valve)")

    mock_connection.mock_coil_update(climate.mixing_valve_state, 20)
    mock_connection.mock_coil_update(unit.cooling_with_room_sensor, "OFF")
    assert hass.states.get(entity_id) == snapshot(name="heating (only)")

    mock_connection.mock_coil_update(climate.use_room_sensor, "OFF")
    assert hass.states.get(entity_id) == snapshot(name="heating (auto)")

    mock_connection.mock_coil_update(unit.prio, None)
    assert hass.states.get(entity_id) == snapshot(name="off (auto)")

    coils.clear()
    assert hass.states.get(entity_id) == snapshot(name="unavailable")