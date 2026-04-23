async def test_hmip_light_hs(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipLight with HS color mode."""
    entity_id = "light.rgbw_controller_channel1"
    entity_name = "RGBW Controller Channel1"
    device_model = "HmIP-RGBW"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["RGBW Controller"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_ON
    assert ha_state.attributes[ATTR_COLOR_MODE] == ColorMode.HS
    assert ha_state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.HS]

    service_call_counter = len(hmip_device.functionalChannels[1].mock_calls)

    # Test turning on with HS color
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, ATTR_HS_COLOR: [240.0, 100.0]},
        blocking=True,
    )
    assert len(hmip_device.functionalChannels[1].mock_calls) == service_call_counter + 1
    assert (
        hmip_device.functionalChannels[1].mock_calls[-1][0]
        == "set_hue_saturation_dim_level_async"
    )
    assert hmip_device.functionalChannels[1].mock_calls[-1][2] == {
        "hue": 240.0,
        "saturation_level": 1.0,
        "dim_level": 0.68,
    }

    # Test turning on with HS color
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, ATTR_HS_COLOR: [220.0, 80.0], ATTR_BRIGHTNESS: 123},
        blocking=True,
    )
    assert len(hmip_device.functionalChannels[1].mock_calls) == service_call_counter + 2
    assert (
        hmip_device.functionalChannels[1].mock_calls[-1][0]
        == "set_hue_saturation_dim_level_async"
    )
    assert hmip_device.functionalChannels[1].mock_calls[-1][2] == {
        "hue": 220.0,
        "saturation_level": 0.8,
        "dim_level": 0.48,
    }

    # Test turning on with HS color
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, ATTR_BRIGHTNESS: 40},
        blocking=True,
    )
    assert len(hmip_device.functionalChannels[1].mock_calls) == service_call_counter + 3
    assert (
        hmip_device.functionalChannels[1].mock_calls[-1][0]
        == "set_hue_saturation_dim_level_async"
    )
    assert hmip_device.functionalChannels[1].mock_calls[-1][2] == {
        "hue": hmip_device.functionalChannels[1].hue,
        "saturation_level": hmip_device.functionalChannels[1].saturationLevel,
        "dim_level": 0.16,
    }