async def test_battery_service(
    hass: HomeAssistant, hk_driver, caplog: pytest.LogCaptureFixture
) -> None:
    """Test battery service."""
    entity_id = "homekit.accessory"
    hass.states.async_set(entity_id, None, {ATTR_BATTERY_LEVEL: 50})
    await hass.async_block_till_done()

    acc = HomeAccessory(hass, hk_driver, "Battery Service", entity_id, 2, None)
    assert acc._char_battery.value == 0
    assert acc._char_low_battery.value == 0
    assert acc._char_charging.value == 2

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

    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        hass.states.async_set(entity_id, None, {ATTR_BATTERY_LEVEL: 15})
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        mock_async_update_state.assert_called_with(state)

    assert acc._char_battery.value == 15
    assert acc._char_low_battery.value == 1
    assert acc._char_charging.value == 2

    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        hass.states.async_set(entity_id, None, {ATTR_BATTERY_LEVEL: "error"})
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        mock_async_update_state.assert_called_with(state)

    assert acc._char_battery.value == 15
    assert acc._char_low_battery.value == 1
    assert acc._char_charging.value == 2
    assert "ERROR" not in caplog.text

    # Test charging
    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        hass.states.async_set(
            entity_id, None, {ATTR_BATTERY_LEVEL: 10, ATTR_BATTERY_CHARGING: True}
        )
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        mock_async_update_state.assert_called_with(state)

    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ):
        acc = HomeAccessory(hass, hk_driver, "Battery Service", entity_id, 3, None)
        assert acc._char_battery.value == 0
        assert acc._char_low_battery.value == 0
        assert acc._char_charging.value == 2

    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        acc.run()
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        mock_async_update_state.assert_called_with(state)
    assert acc._char_battery.value == 10
    assert acc._char_low_battery.value == 1
    assert acc._char_charging.value == 1

    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ):
        hass.states.async_set(
            entity_id, None, {ATTR_BATTERY_LEVEL: 100, ATTR_BATTERY_CHARGING: False}
        )
        await hass.async_block_till_done()
    assert acc._char_battery.value == 100
    assert acc._char_low_battery.value == 0
    assert acc._char_charging.value == 0