async def test_hmip_shutter_contact(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipShutterContact."""
    entity_id = "binary_sensor.fenstergriffsensor"
    entity_name = "Fenstergriffsensor"
    device_model = "HmIP-SRH"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_ON
    assert ha_state.attributes[ATTR_WINDOW_STATE] == WindowState.TILTED

    await async_manipulate_test_data(hass, hmip_device, "windowState", WindowState.OPEN)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_ON
    assert ha_state.attributes[ATTR_WINDOW_STATE] == WindowState.OPEN

    await async_manipulate_test_data(
        hass, hmip_device, "windowState", WindowState.CLOSED
    )
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_OFF
    assert not ha_state.attributes.get(ATTR_WINDOW_STATE)

    await async_manipulate_test_data(hass, hmip_device, "windowState", None)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_UNKNOWN

    # test common attributes
    assert ha_state.attributes[ATTR_RSSI_DEVICE] == -54
    assert not ha_state.attributes.get(ATTR_SABOTAGE)
    await async_manipulate_test_data(hass, hmip_device, "sabotage", True)
    ha_state = hass.states.get(entity_id)
    assert ha_state.attributes[ATTR_SABOTAGE]