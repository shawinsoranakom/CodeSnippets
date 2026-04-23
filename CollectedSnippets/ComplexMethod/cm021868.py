async def test_hmip_combination_signalling_light(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipCombinationSignallingLight (HmIP-MP3P)."""
    entity_id = "light.kombisignalmelder"
    entity_name = "Kombisignalmelder"
    device_model = "HmIP-MP3P"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Kombisignalmelder"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    # Fixture has dimLevel=0.5, simpleRGBColorState=RED, on=true
    assert ha_state.state == STATE_ON
    assert ha_state.attributes[ATTR_COLOR_MODE] == ColorMode.HS
    assert ha_state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.HS]
    assert ha_state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert ha_state.attributes[ATTR_BRIGHTNESS] == 127  # 0.5 * 255
    assert ha_state.attributes[ATTR_HS_COLOR] == (0.0, 100.0)  # RED

    functional_channel = hmip_device.functionalChannels[1]
    service_call_counter = len(functional_channel.mock_calls)

    # Test turn_on with color and brightness
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, ATTR_HS_COLOR: [240.0, 100.0], ATTR_BRIGHTNESS: 255},
        blocking=True,
    )
    assert functional_channel.mock_calls[-1][0] == "set_rgb_dim_level_async"
    assert functional_channel.mock_calls[-1][2] == {
        "rgb_color_state": "BLUE",
        "dim_level": 1.0,
    }
    assert len(functional_channel.mock_calls) == service_call_counter + 1

    # Test turn_off
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": entity_id},
        blocking=True,
    )
    assert functional_channel.mock_calls[-1][0] == "turn_off_async"
    assert len(functional_channel.mock_calls) == service_call_counter + 2

    # Test state update when turned off
    await async_manipulate_test_data(hass, hmip_device, "on", False, channel=1)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_OFF