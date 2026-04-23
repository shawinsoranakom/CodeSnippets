async def test_linked_battery_sensor(
    hass: HomeAssistant, hk_driver, caplog: pytest.LogCaptureFixture
) -> None:
    """Test battery service with linked_battery_sensor."""
    entity_id = "homekit.accessory"
    linked_battery = "sensor.battery"
    hass.states.async_set(entity_id, "open", {ATTR_BATTERY_LEVEL: 100})
    hass.states.async_set(linked_battery, 50, None)
    await hass.async_block_till_done()

    acc = HomeAccessory(
        hass,
        hk_driver,
        "Battery Service",
        entity_id,
        2,
        {CONF_LINKED_BATTERY_SENSOR: linked_battery},
    )
    assert acc.linked_battery_sensor == linked_battery

    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        acc.run()
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        mock_async_update_state.assert_called_with(state)
    assert acc._char_battery.value == 50
    assert acc._char_low_battery.value == 0
    assert acc._char_charging.value == 2

    hass.states.async_set(linked_battery, 10, None)
    await hass.async_block_till_done()
    assert acc._char_battery.value == 10
    assert acc._char_low_battery.value == 1

    # Ignore battery change on entity if it has linked_battery
    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ):
        hass.states.async_set(entity_id, "open", {ATTR_BATTERY_LEVEL: 90})
        await hass.async_block_till_done()
    assert acc._char_battery.value == 10

    # Test none numeric state for linked_battery
    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ):
        hass.states.async_set(linked_battery, "error", None)
        await hass.async_block_till_done()
    assert acc._char_battery.value == 10
    assert "ERROR" not in caplog.text

    # Test charging & low battery threshold
    hass.states.async_set(linked_battery, 20, {ATTR_BATTERY_CHARGING: True})
    await hass.async_block_till_done()

    acc = HomeAccessory(
        hass,
        hk_driver,
        "Battery Service",
        entity_id,
        3,
        {CONF_LINKED_BATTERY_SENSOR: linked_battery, CONF_LOW_BATTERY_THRESHOLD: 50},
    )
    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        acc.run()
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        mock_async_update_state.assert_called_with(state)
    assert acc._char_battery.value == 20
    assert acc._char_low_battery.value == 1
    assert acc._char_charging.value == 1

    hass.states.async_set(linked_battery, 100, {ATTR_BATTERY_CHARGING: False})
    await hass.async_block_till_done()
    assert acc._char_battery.value == 100
    assert acc._char_low_battery.value == 0
    assert acc._char_charging.value == 0

    hass.states.async_remove(linked_battery)
    await hass.async_block_till_done()
    assert acc._char_battery.value == 100
    assert acc._char_low_battery.value == 0
    assert acc._char_charging.value == 0