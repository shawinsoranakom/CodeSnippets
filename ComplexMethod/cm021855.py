async def test_hmip_windspeed_sensor(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipWindspeedSensor."""
    entity_id = "sensor.wettersensor_pro_windspeed"
    entity_name = "Wettersensor - pro Windspeed"
    device_model = "HmIP-SWO-PR"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Wettersensor - pro"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == "2.6"
    assert (
        ha_state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfSpeed.KILOMETERS_PER_HOUR
    )
    assert ha_state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    await async_manipulate_test_data(hass, hmip_device, "windSpeed", 9.4)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == "9.4"

    assert ha_state.attributes[ATTR_WIND_DIRECTION_VARIATION] == 56.25
    assert ha_state.attributes[ATTR_WIND_DIRECTION] == "WNW"

    wind_directions = {
        25: "NNE",
        37.5: "NE",
        70: "ENE",
        92.5: "E",
        115: "ESE",
        137.5: "SE",
        160: "SSE",
        182.5: "S",
        205: "SSW",
        227.5: "SW",
        250: "WSW",
        272.5: UnitOfPower.WATT,
        295: "WNW",
        317.5: "NW",
        340: "NNW",
        0: "N",
    }

    for direction, txt in wind_directions.items():
        await async_manipulate_test_data(hass, hmip_device, "windDirection", direction)
        ha_state = hass.states.get(entity_id)
        assert ha_state.attributes[ATTR_WIND_DIRECTION] == txt