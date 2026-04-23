async def test_aemet_forecast_create_sensors(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test creation of forecast sensors."""

    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    await async_init_integration(hass)

    state = hass.states.get("sensor.aemet_daily_forecast_condition")
    assert state.state == ATTR_CONDITION_SNOWY

    state = hass.states.get("sensor.aemet_daily_forecast_precipitation_probability")
    assert state.state == "0"

    state = hass.states.get("sensor.aemet_daily_forecast_temperature")
    assert state.state == "2"

    state = hass.states.get("sensor.aemet_daily_forecast_temperature_low")
    assert state.state == "-1"

    state = hass.states.get("sensor.aemet_daily_forecast_time")
    assert (
        state.state == dt_util.parse_datetime("2021-01-08 23:00:00+00:00").isoformat()
    )

    state = hass.states.get("sensor.aemet_daily_forecast_wind_bearing")
    assert state.state == "90.0"

    state = hass.states.get("sensor.aemet_daily_forecast_wind_speed")
    assert state.state == "0"

    state = hass.states.get("sensor.aemet_hourly_forecast_condition")
    assert state is None

    state = hass.states.get("sensor.aemet_hourly_forecast_precipitation")
    assert state is None

    state = hass.states.get("sensor.aemet_hourly_forecast_precipitation_probability")
    assert state is None

    state = hass.states.get("sensor.aemet_hourly_forecast_temperature")
    assert state is None

    state = hass.states.get("sensor.aemet_hourly_forecast_temperature_low")
    assert state is None

    state = hass.states.get("sensor.aemet_hourly_forecast_time")
    assert state is None

    state = hass.states.get("sensor.aemet_hourly_forecast_wind_bearing")
    assert state is None

    state = hass.states.get("sensor.aemet_hourly_forecast_wind_max_speed")
    assert state is None

    state = hass.states.get("sensor.aemet_hourly_forecast_wind_speed")
    assert state is None