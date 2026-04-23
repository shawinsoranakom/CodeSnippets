async def test_hmip_security_zone_sensor_group(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipSecurityZoneSensorGroup."""
    entity_id = "binary_sensor.internal_securityzone"
    entity_name = "INTERNAL SecurityZone"
    device_model = "HmIP-SecurityZone"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_groups=["INTERNAL"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_OFF
    assert not ha_state.attributes.get(ATTR_MOTION_DETECTED)
    assert not ha_state.attributes.get(ATTR_PRESENCE_DETECTED)
    assert not ha_state.attributes.get(ATTR_GROUP_MEMBER_UNREACHABLE)
    assert not ha_state.attributes.get(ATTR_SABOTAGE)
    assert not ha_state.attributes.get(ATTR_WINDOW_STATE)

    await async_manipulate_test_data(hass, hmip_device, "motionDetected", True)
    await async_manipulate_test_data(hass, hmip_device, "presenceDetected", True)
    await async_manipulate_test_data(hass, hmip_device, "unreach", True)
    await async_manipulate_test_data(hass, hmip_device, "sabotage", True)
    await async_manipulate_test_data(hass, hmip_device, "windowState", WindowState.OPEN)
    ha_state = hass.states.get(entity_id)

    assert ha_state.state == STATE_ON
    assert ha_state.attributes[ATTR_MOTION_DETECTED]
    assert ha_state.attributes[ATTR_PRESENCE_DETECTED]
    assert ha_state.attributes[ATTR_GROUP_MEMBER_UNREACHABLE]
    assert ha_state.attributes[ATTR_SABOTAGE]
    assert ha_state.attributes[ATTR_WINDOW_STATE] == WindowState.OPEN