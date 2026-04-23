async def test_bus(hass: HomeAssistant) -> None:
    """Test for operational uk_transport sensor with proper attributes."""
    with requests_mock.Mocker() as mock_req:
        uri = re.compile(UkTransportSensor.TRANSPORT_API_URL_BASE + "*")
        mock_req.get(uri, text=await async_load_fixture(hass, "uk_transport/bus.json"))
        assert await async_setup_component(hass, "sensor", VALID_CONFIG)
        await hass.async_block_till_done()

    bus_state = hass.states.get("sensor.next_bus_to_wantage")
    assert None is not bus_state
    assert bus_state.name == f"Next bus to {BUS_DIRECTION}"
    assert bus_state.attributes[ATTR_ATCOCODE] == BUS_ATCOCODE
    assert bus_state.attributes[ATTR_LOCALITY] == "Harwell Campus"
    assert bus_state.attributes[ATTR_STOP_NAME] == "Bus Station"
    assert len(bus_state.attributes.get(ATTR_NEXT_BUSES)) == 2

    direction_re = re.compile(BUS_DIRECTION)
    for bus in bus_state.attributes.get(ATTR_NEXT_BUSES):
        assert None is not bus
        assert None is not direction_re.search(bus["direction"])