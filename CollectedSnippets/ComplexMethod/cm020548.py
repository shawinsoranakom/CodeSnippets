async def test_binary_sensor(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test setup and state change of a binary sensor device."""
    entry = configure_integration(hass)
    test_gateway = HomeControlMockBinarySensor()
    test_gateway.devices["Test"].status = 0
    with patch(
        "homeassistant.components.devolo_home_control.HomeControl",
        side_effect=[test_gateway, HomeControlMock()],
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get(f"{BINARY_SENSOR_DOMAIN}.test_door")
    assert state == snapshot
    assert entity_registry.async_get(f"{BINARY_SENSOR_DOMAIN}.test_door") == snapshot

    state = hass.states.get(f"{BINARY_SENSOR_DOMAIN}.test_overload")
    assert state == snapshot
    assert (
        entity_registry.async_get(f"{BINARY_SENSOR_DOMAIN}.test_overload") == snapshot
    )

    # Emulate websocket message: sensor turned on
    test_gateway.publisher.dispatch("Test", ("Test", True))
    await hass.async_block_till_done()
    assert hass.states.get(f"{BINARY_SENSOR_DOMAIN}.test_door").state == STATE_ON

    # Emulate websocket message: device went offline
    test_gateway.devices["Test"].status = 1
    test_gateway.publisher.dispatch("Test", ("Status", False, "status"))
    await hass.async_block_till_done()
    assert (
        hass.states.get(f"{BINARY_SENSOR_DOMAIN}.test_door").state == STATE_UNAVAILABLE
    )

    # Emulate websocket message: device was deleted
    test_gateway.publisher.dispatch("Test", ("Test", "del"))
    await hass.async_block_till_done()
    device = device_registry.async_get_device(identifiers={(DOMAIN, "Test")})
    assert not device