async def test_hmip_din_rail_dimmer_3_channel3(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicIP DinRailDimmer3 Channel 3."""
    entity_id = "light.3_dimmer_esstisch"
    entity_name = "3-Dimmer Esstisch"
    device_model = "HmIP-DRDI3"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["3-Dimmer"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_ON
    assert ha_state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.BRIGHTNESS]
    assert ha_state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    service_call_counter = len(hmip_device.mock_calls)

    await hass.services.async_call(
        "light", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert hmip_device.mock_calls[-1][0] == "set_dim_level_async"
    assert hmip_device.mock_calls[-1][1] == (1, 3)

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, "brightness": "100"},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 2
    assert hmip_device.mock_calls[-1][0] == "set_dim_level_async"
    assert hmip_device.mock_calls[-1][1] == (0.39215686274509803, 3)
    await async_manipulate_test_data(hass, hmip_device, "dimLevel", 1, channel=3)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_ON
    assert ha_state.attributes[ATTR_BRIGHTNESS] == 255
    assert ha_state.attributes[ATTR_COLOR_MODE] == ColorMode.BRIGHTNESS
    assert ha_state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.BRIGHTNESS]
    assert ha_state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    await hass.services.async_call(
        "light", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 4
    assert hmip_device.mock_calls[-1][0] == "set_dim_level_async"
    assert hmip_device.mock_calls[-1][1] == (0, 3)
    await async_manipulate_test_data(hass, hmip_device, "dimLevel", 0, channel=3)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_OFF

    await async_manipulate_test_data(hass, hmip_device, "dimLevel", None, channel=3)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_OFF
    assert not ha_state.attributes.get(ATTR_BRIGHTNESS)