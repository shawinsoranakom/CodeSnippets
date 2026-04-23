async def test_linked_battery_charging_sensor(
    hass: HomeAssistant, hk_driver, caplog: pytest.LogCaptureFixture
) -> None:
    """Test battery service with linked_battery_charging_sensor."""
    entity_id = "homekit.accessory"
    linked_battery_charging_sensor = "binary_sensor.battery_charging"
    hass.states.async_set(entity_id, "open", {ATTR_BATTERY_LEVEL: 100})
    hass.states.async_set(linked_battery_charging_sensor, STATE_ON, None)
    await hass.async_block_till_done()

    acc = HomeAccessory(
        hass,
        hk_driver,
        "Battery Service",
        entity_id,
        2,
        {CONF_LINKED_BATTERY_CHARGING_SENSOR: linked_battery_charging_sensor},
    )
    assert acc.linked_battery_charging_sensor == linked_battery_charging_sensor

    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        acc.run()
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        mock_async_update_state.assert_called_with(state)
    assert acc._char_battery.value == 100
    assert acc._char_low_battery.value == 0
    assert acc._char_charging.value == 1

    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        hass.states.async_set(linked_battery_charging_sensor, STATE_OFF, None)
        acc.run()
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        mock_async_update_state.assert_called_with(state)
    assert acc._char_charging.value == 0

    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        hass.states.async_set(linked_battery_charging_sensor, STATE_ON, None)
        acc.run()
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        mock_async_update_state.assert_called_with(state)
    assert acc._char_charging.value == 1

    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        hass.states.async_remove(linked_battery_charging_sensor)
        acc.run()
        await hass.async_block_till_done()
    assert acc._char_charging.value == 1