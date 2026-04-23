async def test_hmip_heating_group_heat(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipHeatingGroup."""
    entity_id = "climate.badezimmer"
    entity_name = "Badezimmer"
    device_model = None
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Wandthermostat", "Heizkörperthermostat3"],
        test_groups=[entity_name],
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == HVACMode.AUTO
    assert ha_state.attributes["current_temperature"] == 23.8
    assert ha_state.attributes["min_temp"] == 5.0
    assert ha_state.attributes["max_temp"] == 30.0
    assert ha_state.attributes["temperature"] == 5.0
    assert ha_state.attributes["current_humidity"] == 47
    assert ha_state.attributes[ATTR_PRESET_MODE] == "STD"
    assert ha_state.attributes[ATTR_PRESET_MODES] == [
        PRESET_BOOST,
        PRESET_ECO,
        "STD",
        "Winter",
    ]

    service_call_counter = len(hmip_device.mock_calls)

    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": entity_id, "temperature": 22.5},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "set_point_temperature_async"
    assert hmip_device.mock_calls[-1][1] == (22.5,)
    await async_manipulate_test_data(hass, hmip_device, "actualTemperature", 22.5)
    ha_state = hass.states.get(entity_id)
    assert ha_state.attributes[ATTR_CURRENT_TEMPERATURE] == 22.5

    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": entity_id, "hvac_mode": HVACMode.HEAT},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "set_control_mode_async"
    assert hmip_device.mock_calls[-1][1] == ("MANUAL",)
    await async_manipulate_test_data(hass, hmip_device, "controlMode", "MANUAL")
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == HVACMode.HEAT

    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": entity_id, "hvac_mode": HVACMode.AUTO},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 5
    assert hmip_device.mock_calls[-1][0] == "set_control_mode_async"
    assert hmip_device.mock_calls[-1][1] == ("AUTOMATIC",)
    await async_manipulate_test_data(hass, hmip_device, "controlMode", "AUTO")
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == HVACMode.AUTO

    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {"entity_id": entity_id, "preset_mode": PRESET_BOOST},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 7
    assert hmip_device.mock_calls[-1][0] == "set_boost_async"
    assert hmip_device.mock_calls[-1][1] == ()
    await async_manipulate_test_data(hass, hmip_device, "boostMode", True)
    ha_state = hass.states.get(entity_id)
    assert ha_state.attributes[ATTR_PRESET_MODE] == PRESET_BOOST

    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {"entity_id": entity_id, "preset_mode": "STD"},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 11
    assert hmip_device.mock_calls[-1][0] == "set_active_profile_async"
    assert hmip_device.mock_calls[-1][1] == (0,)
    await async_manipulate_test_data(hass, hmip_device, "boostMode", False)
    ha_state = hass.states.get(entity_id)
    assert ha_state.attributes[ATTR_PRESET_MODE] == "STD"

    # No new service call should be in mock_calls.
    assert len(hmip_device.mock_calls) == service_call_counter + 12
    # Only fire event from last async_manipulate_test_data available.
    assert hmip_device.mock_calls[-1][0] == "fire_update_event"

    await async_manipulate_test_data(hass, hmip_device, "controlMode", "ECO")
    await async_manipulate_test_data(
        hass,
        mock_hap.home.get_functionalHome(IndoorClimateHome),
        "absenceType",
        AbsenceType.VACATION,
        fire_device=hmip_device,
    )
    ha_state = hass.states.get(entity_id)
    assert ha_state.attributes[ATTR_PRESET_MODE] == PRESET_AWAY

    await async_manipulate_test_data(hass, hmip_device, "controlMode", "ECO")
    await async_manipulate_test_data(
        hass,
        mock_hap.home.get_functionalHome(IndoorClimateHome),
        "absenceType",
        AbsenceType.PERIOD,
        fire_device=hmip_device,
    )
    ha_state = hass.states.get(entity_id)
    assert ha_state.attributes[ATTR_PRESET_MODE] == PRESET_ECO

    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {"entity_id": entity_id, "preset_mode": "Winter"},
        blocking=True,
    )

    assert len(hmip_device.mock_calls) == service_call_counter + 18
    assert hmip_device.mock_calls[-1][0] == "set_active_profile_async"
    assert hmip_device.mock_calls[-1][1] == (1,)

    mock_hap.home.get_functionalHome(
        IndoorClimateHome
    ).absenceType = AbsenceType.PERMANENT
    await async_manipulate_test_data(hass, hmip_device, "controlMode", "ECO")

    ha_state = hass.states.get(entity_id)
    assert ha_state.attributes[ATTR_PRESET_END_TIME] == PERMANENT_END_TIME

    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": entity_id, "hvac_mode": HVACMode.HEAT},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 20
    assert hmip_device.mock_calls[-1][0] == "set_control_mode_async"
    assert hmip_device.mock_calls[-1][1] == ("MANUAL",)
    await async_manipulate_test_data(hass, hmip_device, "controlMode", "MANUAL")
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == HVACMode.HEAT

    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {"entity_id": entity_id, "preset_mode": "Winter"},
        blocking=True,
    )

    assert len(hmip_device.mock_calls) == service_call_counter + 23
    assert hmip_device.mock_calls[-1][0] == "set_active_profile_async"
    assert hmip_device.mock_calls[-1][1] == (1,)
    hmip_device.activeProfile = hmip_device.profiles[0]
    await async_manipulate_test_data(hass, hmip_device, "controlMode", "AUTOMATIC")
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == HVACMode.AUTO

    # hvac mode "dry" is not available.
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "climate",
            "set_hvac_mode",
            {"entity_id": entity_id, "hvac_mode": "dry"},
            blocking=True,
        )

    assert len(hmip_device.mock_calls) == service_call_counter + 24
    # Only fire event from last async_manipulate_test_data available.
    assert hmip_device.mock_calls[-1][0] == "fire_update_event"

    assert ha_state.state == HVACMode.AUTO
    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {"entity_id": entity_id, "preset_mode": PRESET_ECO},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 25
    assert hmip_device.mock_calls[-1][0] == "set_control_mode_async"
    assert hmip_device.mock_calls[-1][1] == ("ECO",)
    await async_manipulate_test_data(hass, hmip_device, "controlMode", "ECO")
    ha_state = hass.states.get(entity_id)
    assert ha_state.attributes[ATTR_PRESET_MODE] == PRESET_ECO
    assert ha_state.state == HVACMode.AUTO

    await async_manipulate_test_data(hass, hmip_device, "floorHeatingMode", "RADIATOR")
    await async_manipulate_test_data(hass, hmip_device, "valvePosition", 0.1)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == HVACMode.AUTO
    assert ha_state.attributes[ATTR_HVAC_ACTION] == HVACAction.HEATING
    await async_manipulate_test_data(hass, hmip_device, "floorHeatingMode", "RADIATOR")
    await async_manipulate_test_data(hass, hmip_device, "valvePosition", 0.0)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == HVACMode.AUTO
    assert ha_state.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE