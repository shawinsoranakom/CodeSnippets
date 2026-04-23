async def test_sensor(hass: HomeAssistant) -> None:
    """Test that sensor works."""
    assert hass.states.get("sensor.waze_travel_time").state == "150"
    assert (
        hass.states.get("sensor.waze_travel_time").attributes["attribution"]
        == "Powered by Waze"
    )
    assert hass.states.get("sensor.waze_travel_time").attributes["duration"] == 150
    assert hass.states.get("sensor.waze_travel_time").attributes["distance"] == 300
    assert (
        hass.states.get("sensor.waze_travel_time").attributes["route"]
        == "E1337 - Teststreet"
    )
    assert (
        hass.states.get("sensor.waze_travel_time").attributes["origin"] == "location1"
    )
    assert (
        hass.states.get("sensor.waze_travel_time").attributes["destination"]
        == "location2"
    )
    assert (
        hass.states.get("sensor.waze_travel_time").attributes["unit_of_measurement"]
        == "min"
    )