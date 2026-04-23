async def test_battery_sensor_updates_on_schedule(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test the battery sensor refreshes naturally on its polling interval."""
    instance = MockBridge()

    def factory(*args: Any, **kwargs: Any) -> MockBridge:
        """Return the mock bridge instance."""
        return instance

    original_get_battery_status = instance.get_battery_status
    instance.get_battery_status = AsyncMock(side_effect=original_get_battery_status)

    await async_setup_integration(hass, factory)
    await hass.async_block_till_done()

    binary_sensor_entity_id = "binary_sensor.basement_bedroom_left_shade_battery"
    initial_state = hass.states.get(binary_sensor_entity_id)
    assert initial_state is not None
    assert initial_state.state == STATE_OFF
    assert initial_state.name == "Basement Bedroom Left Shade Battery"
    assert (
        initial_state.attributes[ATTR_DEVICE_CLASS] == BinarySensorDeviceClass.BATTERY
    )

    instance.battery_statuses["802"] = " Low "
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    updated_state = hass.states.get(binary_sensor_entity_id)
    assert updated_state is not None
    assert updated_state.state == STATE_ON
    assert instance.get_battery_status.await_count == 2
    instance.get_battery_status.assert_awaited_with("802")

    instance.battery_statuses["802"] = "Unknown"
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    unknown_state = hass.states.get(binary_sensor_entity_id)
    assert unknown_state is not None
    assert unknown_state.state == STATE_UNKNOWN
    assert instance.get_battery_status.await_count == 3