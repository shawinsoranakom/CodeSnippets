async def test_hmip_heating_group_cool(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipHeatingGroup."""
    entity_id = "climate.badezimmer"
    entity_name = "Badezimmer"
    device_model = None
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_groups=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    hmip_device.activeProfile = hmip_device.profiles[3]
    await async_manipulate_test_data(hass, hmip_device, "cooling", True)
    await async_manipulate_test_data(hass, hmip_device, "coolingAllowed", True)
    await async_manipulate_test_data(hass, hmip_device, "coolingIgnored", False)
    ha_state = hass.states.get(entity_id)

    assert ha_state.state == HVACMode.AUTO
    assert ha_state.attributes["current_temperature"] == 23.8
    assert ha_state.attributes["min_temp"] == 5.0
    assert ha_state.attributes["max_temp"] == 30.0
    assert ha_state.attributes["temperature"] == 5.0
    assert ha_state.attributes["current_humidity"] == 47
    assert ha_state.attributes[ATTR_PRESET_MODE] == "Cool1"
    assert ha_state.attributes[ATTR_PRESET_MODES] == ["Cool1", "Cool2"]

    service_call_counter = len(hmip_device.mock_calls)

    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": entity_id, "hvac_mode": HVACMode.COOL},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "set_control_mode_async"
    assert hmip_device.mock_calls[-1][1] == ("MANUAL",)
    await async_manipulate_test_data(hass, hmip_device, "controlMode", "MANUAL")
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == HVACMode.COOL

    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": entity_id, "hvac_mode": HVACMode.AUTO},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "set_control_mode_async"
    assert hmip_device.mock_calls[-1][1] == ("AUTOMATIC",)
    await async_manipulate_test_data(hass, hmip_device, "controlMode", "AUTO")
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == HVACMode.AUTO

    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {"entity_id": entity_id, "preset_mode": "Cool2"},
        blocking=True,
    )

    assert len(hmip_device.mock_calls) == service_call_counter + 6
    assert hmip_device.mock_calls[-1][0] == "set_active_profile_async"
    assert hmip_device.mock_calls[-1][1] == (4,)

    hmip_device.activeProfile = hmip_device.profiles[4]
    await async_manipulate_test_data(hass, hmip_device, "cooling", True)
    await async_manipulate_test_data(hass, hmip_device, "coolingAllowed", False)
    await async_manipulate_test_data(hass, hmip_device, "coolingIgnored", False)
    ha_state = hass.states.get(entity_id)

    assert ha_state.state == HVACMode.OFF
    assert ha_state.attributes[ATTR_PRESET_MODE] == "none"
    assert ha_state.attributes[ATTR_PRESET_MODES] == []

    hmip_device.activeProfile = hmip_device.profiles[4]
    await async_manipulate_test_data(hass, hmip_device, "cooling", True)
    await async_manipulate_test_data(hass, hmip_device, "coolingAllowed", True)
    await async_manipulate_test_data(hass, hmip_device, "coolingIgnored", True)
    ha_state = hass.states.get(entity_id)

    assert ha_state.state == HVACMode.OFF
    assert ha_state.attributes[ATTR_PRESET_MODE] == "none"
    assert ha_state.attributes[ATTR_PRESET_MODES] == []

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "climate",
            "set_preset_mode",
            {"entity_id": entity_id, "preset_mode": "Cool2"},
            blocking=True,
        )

    assert len(hmip_device.mock_calls) == service_call_counter + 12
    # fire_update_event shows that set_active_profile has not been called.
    assert hmip_device.mock_calls[-1][0] == "fire_update_event"

    hmip_device.activeProfile = hmip_device.profiles[4]
    await async_manipulate_test_data(hass, hmip_device, "cooling", True)
    await async_manipulate_test_data(hass, hmip_device, "coolingAllowed", True)
    await async_manipulate_test_data(hass, hmip_device, "coolingIgnored", False)
    ha_state = hass.states.get(entity_id)

    assert ha_state.state == HVACMode.AUTO
    assert ha_state.attributes[ATTR_PRESET_MODE] == "Cool2"
    assert ha_state.attributes[ATTR_PRESET_MODES] == ["Cool1", "Cool2"]

    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {"entity_id": entity_id, "preset_mode": "Cool2"},
        blocking=True,
    )

    assert len(hmip_device.mock_calls) == service_call_counter + 17
    assert hmip_device.mock_calls[-1][0] == "set_active_profile_async"
    assert hmip_device.mock_calls[-1][1] == (4,)