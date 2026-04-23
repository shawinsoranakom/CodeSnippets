async def test_hmip_wired_push_button_led_2(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipOpticalSignalLight second LED."""
    entity_id = "light.wired_taster_6_fach_led_2"
    entity_name = "Wired Taster 6-fach LED 2"
    device_model = "HmIPW-WRC6"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Wired Taster 6-fach"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_OFF
    assert ha_state.attributes[ATTR_COLOR_MODE] is None
    assert ha_state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.HS]
    assert ha_state.attributes[ATTR_SUPPORTED_FEATURES] == LightEntityFeature.EFFECT

    service_call_counter = len(hmip_device.mock_calls)

    # Test turning on second LED
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )
    assert hmip_device.mock_calls[-1][0] == "set_optical_signal_async"
    assert hmip_device.mock_calls[-1][2]["channelIndex"] == 8
    assert len(hmip_device.mock_calls) == service_call_counter + 1