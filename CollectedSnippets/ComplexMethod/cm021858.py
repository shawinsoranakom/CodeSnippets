async def test_hmip_notification_light(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipNotificationLight."""
    entity_id = "light.treppe_alarm_status"
    entity_name = "Treppe Alarm Status"
    device_model = "HmIP-BSL"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Treppe"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_OFF
    assert ha_state.attributes[ATTR_COLOR_MODE] is None
    assert ha_state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.HS]
    assert ha_state.attributes[ATTR_SUPPORTED_FEATURES] == LightEntityFeature.TRANSITION
    service_call_counter = len(hmip_device.mock_calls)

    # Send all color via service call.
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, "brightness_pct": "100", "transition": 100},
        blocking=True,
    )
    assert hmip_device.mock_calls[-1][0] == "set_rgb_dim_level_with_time_async"
    assert hmip_device.mock_calls[-1][2] == {
        "channelIndex": 2,
        "rgb": "RED",
        "dimLevel": 1.0,
        "onTime": 0,
        "rampTime": 100.0,
    }

    color_list = {
        RGBColorState.WHITE: [0.0, 0.0],
        RGBColorState.RED: [0.0, 100.0],
        RGBColorState.YELLOW: [60.0, 100.0],
        RGBColorState.GREEN: [120.0, 100.0],
        RGBColorState.TURQUOISE: [180.0, 100.0],
        RGBColorState.BLUE: [240.0, 100.0],
        RGBColorState.PURPLE: [300.0, 100.0],
    }

    for color, hs_color in color_list.items():
        await hass.services.async_call(
            "light",
            "turn_on",
            {"entity_id": entity_id, "hs_color": hs_color},
            blocking=True,
        )
        assert hmip_device.mock_calls[-1][0] == "set_rgb_dim_level_with_time_async"
        assert hmip_device.mock_calls[-1][2] == {
            "channelIndex": 2,
            "dimLevel": 0.0392156862745098,
            "onTime": 0,
            "rampTime": 0.5,
            "rgb": color,
        }

    assert len(hmip_device.mock_calls) == service_call_counter + 8

    await async_manipulate_test_data(hass, hmip_device, "dimLevel", 1, 2)
    await async_manipulate_test_data(
        hass, hmip_device, "simpleRGBColorState", RGBColorState.PURPLE, 2
    )
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_ON
    assert ha_state.attributes[ATTR_COLOR_NAME] == RGBColorState.PURPLE
    assert ha_state.attributes[ATTR_BRIGHTNESS] == 255
    assert ha_state.attributes[ATTR_COLOR_MODE] == ColorMode.HS
    assert ha_state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.HS]
    assert ha_state.attributes[ATTR_SUPPORTED_FEATURES] == LightEntityFeature.TRANSITION

    await hass.services.async_call(
        "light", "turn_off", {"entity_id": entity_id, "transition": 100}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 11
    assert hmip_device.mock_calls[-1][0] == "set_rgb_dim_level_with_time_async"
    assert hmip_device.mock_calls[-1][2] == {
        "channelIndex": 2,
        "dimLevel": 0.0,
        "onTime": 0,
        "rampTime": 100,
        "rgb": "PURPLE",
    }
    await async_manipulate_test_data(hass, hmip_device, "dimLevel", 0, 2)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_OFF

    await async_manipulate_test_data(hass, hmip_device, "dimLevel", None, 2)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_OFF
    assert not ha_state.attributes.get(ATTR_BRIGHTNESS)