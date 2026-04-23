async def test_consumption_sensor(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, snapshot: SnapshotAssertion
) -> None:
    """Test setup and state change of a consumption sensor device."""
    entry = configure_integration(hass)
    test_gateway = HomeControlMockConsumption()
    with patch(
        "homeassistant.components.devolo_home_control.HomeControl",
        side_effect=[test_gateway, HomeControlMock()],
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get(f"{SENSOR_DOMAIN}.test_power")
    assert state == snapshot
    assert entity_registry.async_get(f"{SENSOR_DOMAIN}.test_power") == snapshot

    state = hass.states.get(f"{SENSOR_DOMAIN}.test_energy")
    assert state == snapshot
    assert entity_registry.async_get(f"{SENSOR_DOMAIN}.test_energy") == snapshot

    # Emulate websocket message: value changed
    test_gateway.devices["Test"].consumption_property["devolo.Meter:Test"].total = 50.0
    test_gateway.publisher.dispatch("Test", ("devolo.Meter:Test", 50.0))
    await hass.async_block_till_done()
    assert hass.states.get(f"{SENSOR_DOMAIN}.test_energy").state == "50.0"

    # Emulate websocket message: device went offline
    test_gateway.devices["Test"].status = 1
    test_gateway.publisher.dispatch("Test", ("Status", False, "status"))
    await hass.async_block_till_done()
    assert hass.states.get(f"{SENSOR_DOMAIN}.test_power").state == STATE_UNAVAILABLE
    assert hass.states.get(f"{SENSOR_DOMAIN}.test_energy").state == STATE_UNAVAILABLE