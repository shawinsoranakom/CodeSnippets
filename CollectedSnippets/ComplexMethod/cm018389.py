async def test_aemet_weather_create_sensors(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test creation of weather sensors."""

    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    await async_init_integration(hass)

    state = hass.states.get("sensor.aemet_condition")
    assert state.state == ATTR_CONDITION_SNOWY

    state = hass.states.get("sensor.aemet_humidity")
    assert state.state == "99.0"

    state = hass.states.get("sensor.aemet_pressure")
    assert state.state == "1004.4"

    state = hass.states.get("sensor.aemet_rain")
    assert state.state == "7.0"

    state = hass.states.get("sensor.aemet_rain_probability")
    assert state.state == "100"

    state = hass.states.get("sensor.aemet_snow")
    assert state.state == "1.2"

    state = hass.states.get("sensor.aemet_snow_probability")
    assert state.state == "100"

    state = hass.states.get("sensor.aemet_station_id")
    assert state.state == "3195"

    state = hass.states.get("sensor.aemet_station_name")
    assert state.state == "MADRID RETIRO"

    state = hass.states.get("sensor.aemet_station_timestamp")
    assert state.state == "2021-01-09T12:00:00+00:00"

    state = hass.states.get("sensor.aemet_storm_probability")
    assert state.state == "0"

    state = hass.states.get("sensor.aemet_temperature")
    assert state.state == "-0.7"

    state = hass.states.get("sensor.aemet_temperature_feeling")
    assert state.state == "-4"

    state = hass.states.get("sensor.aemet_town_id")
    assert state.state == "id28065"

    state = hass.states.get("sensor.aemet_town_name")
    assert state.state == "Getafe"

    state = hass.states.get("sensor.aemet_town_timestamp")
    assert state.state == "2021-01-09T11:47:45+00:00"

    state = hass.states.get("sensor.aemet_wind_bearing")
    assert state.state == "122.0"

    state = hass.states.get("sensor.aemet_wind_max_speed")
    assert state.state == "12.2"

    state = hass.states.get("sensor.aemet_wind_speed")
    assert state.state == "3.2"