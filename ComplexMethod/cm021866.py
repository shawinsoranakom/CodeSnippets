async def test_hmip_wired_push_button_led(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipOpticalSignalLight."""
    entity_id = "light.wired_taster_6_fach_led_1"
    entity_name = "Wired Taster 6-fach LED 1"
    device_model = "HmIPW-WRC6"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Wired Taster 6-fach"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_ON
    assert ha_state.attributes[ATTR_COLOR_MODE] == ColorMode.HS
    assert ha_state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.HS]
    assert ha_state.attributes[ATTR_SUPPORTED_FEATURES] == LightEntityFeature.EFFECT
    assert ha_state.attributes[ATTR_BRIGHTNESS] == 127
    assert ha_state.attributes[ATTR_COLOR_NAME] == "GREEN"

    service_call_counter = len(hmip_device.mock_calls)

    # Test turning on with color and brightness
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, ATTR_HS_COLOR: [240.0, 100.0], ATTR_BRIGHTNESS: 128},
        blocking=True,
    )
    assert hmip_device.mock_calls[-1][0] == "set_optical_signal_async"
    assert hmip_device.mock_calls[-1][2] == {
        "channelIndex": 7,
        "opticalSignalBehaviour": OpticalSignalBehaviour.ON,
        "rgb": "BLUE",
        "dimLevel": 0.5,
    }
    assert len(hmip_device.mock_calls) == service_call_counter + 1

    # Test turning on with effect
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, ATTR_EFFECT: "blinking"},
        blocking=True,
    )
    assert hmip_device.mock_calls[-1][0] == "set_optical_signal_async"
    assert (
        hmip_device.mock_calls[-1][2]["opticalSignalBehaviour"]
        == OpticalSignalBehaviour.BLINKING_MIDDLE
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 2