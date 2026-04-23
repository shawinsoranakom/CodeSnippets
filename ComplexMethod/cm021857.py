async def test_hmip_light(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipLight."""
    entity_id = "light.treppe_ch"
    entity_name = "Treppe CH"
    device_model = "HmIP-BSL"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Treppe"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_ON
    assert ha_state.attributes[ATTR_COLOR_MODE] == ColorMode.ONOFF
    assert ha_state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.ONOFF]
    assert ha_state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    service_call_counter = len(hmip_device.mock_calls)
    await hass.services.async_call(
        "light", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "turn_off_async"
    assert hmip_device.mock_calls[-1][1] == ()

    await async_manipulate_test_data(hass, hmip_device, "on", False)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_OFF
    assert ha_state.attributes[ATTR_COLOR_MODE] is None
    assert ha_state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.ONOFF]
    assert ha_state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    await hass.services.async_call(
        "light", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "turn_on_async"
    assert hmip_device.mock_calls[-1][1] == ()

    await async_manipulate_test_data(hass, hmip_device, "on", True)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_ON