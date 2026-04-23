async def test_v4_weather(hass: HomeAssistant, tomorrowio_config_entry_update) -> None:
    """Test v4 weather data."""
    weather_state = await _setup(hass, API_V4_ENTRY_DATA)

    tomorrowio_config_entry_update.assert_called_with(
        [
            "temperature",
            "humidity",
            "pressureSeaLevel",
            "windSpeed",
            "windDirection",
            "weatherCode",
            "visibility",
            "pollutantO3",
            "windGust",
            "cloudCover",
            "precipitationType",
            "pollutantCO",
            "mepIndex",
            "mepHealthConcern",
            "mepPrimaryPollutant",
            "cloudBase",
            "cloudCeiling",
            "cloudCover",
            "dewPoint",
            "epaIndex",
            "epaHealthConcern",
            "epaPrimaryPollutant",
            "temperatureApparent",
            "fireIndex",
            "pollutantNO2",
            "pollutantO3",
            "particulateMatter10",
            "particulateMatter25",
            "grassIndex",
            "treeIndex",
            "weedIndex",
            "precipitationType",
            "pressureSurfaceLevel",
            "solarGHI",
            "pollutantSO2",
            "uvIndex",
            "uvHealthConcern",
            "windGust",
        ],
        [
            "temperatureMin",
            "temperatureMax",
            "dewPoint",
            "humidity",
            "windSpeed",
            "windDirection",
            "weatherCode",
            "precipitationIntensityAvg",
            "precipitationProbability",
        ],
        nowcast_timestep=60,
        location="80.0,80.0",
    )

    assert weather_state.state == ATTR_CONDITION_SUNNY
    assert weather_state.attributes[ATTR_ATTRIBUTION] == ATTRIBUTION
    assert weather_state.attributes[ATTR_FRIENDLY_NAME] == "Tomorrow.io Daily"
    assert weather_state.attributes[ATTR_WEATHER_HUMIDITY] == 23
    assert weather_state.attributes[ATTR_WEATHER_OZONE] == 46.53
    assert weather_state.attributes[ATTR_WEATHER_PRECIPITATION_UNIT] == "mm"
    assert weather_state.attributes[ATTR_WEATHER_PRESSURE] == 30.35
    assert weather_state.attributes[ATTR_WEATHER_PRESSURE_UNIT] == "hPa"
    assert weather_state.attributes[ATTR_WEATHER_TEMPERATURE] == 44.1
    assert weather_state.attributes[ATTR_WEATHER_TEMPERATURE_UNIT] == "°C"
    assert weather_state.attributes[ATTR_WEATHER_VISIBILITY] == 8.15
    assert weather_state.attributes[ATTR_WEATHER_VISIBILITY_UNIT] == "km"
    assert weather_state.attributes[ATTR_WEATHER_WIND_BEARING] == 315.14
    assert weather_state.attributes[ATTR_WEATHER_WIND_SPEED] == 33.59  # 9.33 m/s ->km/h
    assert weather_state.attributes[ATTR_WEATHER_WIND_SPEED_UNIT] == "km/h"