async def test_sensor(hass: HomeAssistant) -> None:
    """Test that sensor works."""
    assert hass.states.get("sensor.google_travel_time").state == "27.0"
    assert (
        hass.states.get("sensor.google_travel_time").attributes["attribution"]
        == "Powered by Google"
    )
    assert (
        hass.states.get("sensor.google_travel_time").attributes["duration"] == "26 mins"
    )
    assert (
        hass.states.get("sensor.google_travel_time").attributes["duration_in_traffic"]
        == "27 mins"
    )
    assert (
        hass.states.get("sensor.google_travel_time").attributes["distance"] == "21.3 km"
    )
    assert (
        hass.states.get("sensor.google_travel_time").attributes["origin"] == "location1"
    )
    assert (
        hass.states.get("sensor.google_travel_time").attributes["destination"]
        == "49.983862755708444,8.223882827079068"
    )
    assert (
        hass.states.get("sensor.google_travel_time").attributes["unit_of_measurement"]
        == "min"
    )