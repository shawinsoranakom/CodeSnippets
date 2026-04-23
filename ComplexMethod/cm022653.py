async def test_missing_linked_battery_sensor(
    hass: HomeAssistant, hk_driver, caplog: pytest.LogCaptureFixture
) -> None:
    """Test battery service with missing linked_battery_sensor."""
    entity_id = "homekit.accessory"
    linked_battery = "sensor.battery"
    hass.states.async_set(entity_id, "open")
    await hass.async_block_till_done()

    acc = HomeAccessory(
        hass,
        hk_driver,
        "Battery Service",
        entity_id,
        2,
        {CONF_LINKED_BATTERY_SENSOR: linked_battery},
    )
    assert not acc.linked_battery_sensor

    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        acc.run()
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        mock_async_update_state.assert_called_with(state)

    assert not acc.linked_battery_sensor
    assert acc._char_battery is None
    assert acc._char_low_battery is None
    assert acc._char_charging is None

    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        hass.states.async_remove(entity_id)
        acc.run()
        await hass.async_block_till_done()

    assert not acc.linked_battery_sensor
    assert acc._char_battery is None
    assert acc._char_low_battery is None
    assert acc._char_charging is None