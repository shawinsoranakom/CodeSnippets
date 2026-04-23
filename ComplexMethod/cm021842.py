async def test_hmip_heating_group_heat_with_switch(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipHeatingGroup."""
    entity_id = "climate.schlafzimmer"
    entity_name = "Schlafzimmer"
    device_model = None
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Wandthermostat", "Heizkörperthermostat", "Pc"],
        test_groups=[entity_name],
    )
    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert hmip_device
    assert ha_state.state == HVACMode.AUTO
    assert ha_state.attributes["current_temperature"] == 24.7
    assert ha_state.attributes["min_temp"] == 5.0
    assert ha_state.attributes["max_temp"] == 30.0
    assert ha_state.attributes["temperature"] == 5.0
    assert ha_state.attributes["current_humidity"] == 43
    assert ha_state.attributes[ATTR_PRESET_MODE] == "STD"
    assert ha_state.attributes[ATTR_PRESET_MODES] == [
        PRESET_BOOST,
        PRESET_ECO,
        "STD",
        "P2",
    ]