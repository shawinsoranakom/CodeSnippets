async def test_water_heater_entity(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_generic_device_entry: MockGenericDeviceEntryType,
) -> None:
    """Test a generic water heater entity."""
    entity_info = [
        WaterHeaterInfo(
            object_id="my_boiler",
            key=1,
            name="My Boiler",
            min_temperature=10.0,
            max_temperature=85.0,
            supported_modes=[
                WaterHeaterMode.ECO,
                WaterHeaterMode.GAS,
            ],
        )
    ]
    states = [
        WaterHeaterState(
            key=1,
            mode=WaterHeaterMode.ECO,
            current_temperature=45.0,
            target_temperature=50.0,
        )
    ]

    await mock_generic_device_entry(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )

    state = hass.states.get("water_heater.test_my_boiler")
    assert state is not None
    assert state.state == "eco"
    assert state.attributes["current_temperature"] == 45.0
    assert state.attributes["temperature"] == 50.0
    assert state.attributes["min_temp"] == 10.0
    assert state.attributes["max_temp"] == 85.0
    assert state.attributes["operation_list"] == ["eco", "gas"]