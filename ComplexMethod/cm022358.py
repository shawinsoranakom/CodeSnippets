async def test_sensors_100(hass: HomeAssistant, setup_rainforest_100) -> None:
    """Test the sensors."""
    assert len(hass.states.async_all()) == 3

    demand = hass.states.get("sensor.eagle_100_power_demand")
    assert demand is not None
    assert demand.state == "1.152000"
    assert demand.attributes["unit_of_measurement"] == "kW"

    delivered = hass.states.get("sensor.eagle_100_total_energy_delivered")
    assert delivered is not None
    assert delivered.state == "45251.285000"
    assert delivered.attributes["unit_of_measurement"] == "kWh"

    received = hass.states.get("sensor.eagle_100_total_energy_received")
    assert received is not None
    assert received.state == "232.232000"
    assert received.attributes["unit_of_measurement"] == "kWh"