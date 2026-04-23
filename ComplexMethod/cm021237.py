async def test_rmvtransport_min_config(hass: HomeAssistant) -> None:
    """Test minimal rmvtransport configuration."""
    with patch(
        "RMVtransport.RMVtransport.get_departures",
        return_value=get_departures_mock(),
    ):
        assert await async_setup_component(hass, "sensor", VALID_CONFIG_MINIMAL) is True
        await hass.async_block_till_done()

    state = hass.states.get("sensor.frankfurt_main_hauptbahnhof")
    assert state.state == "7"
    assert state.attributes["departure_time"] == datetime.datetime(2018, 8, 6, 14, 21)
    assert (
        state.attributes["direction"] == "Frankfurt (Main) Hugo-Junkers-Straße/Schleife"
    )
    assert state.attributes["product"] == "Tram"
    assert state.attributes["line"] == 12
    assert state.attributes["icon"] == "mdi:tram"
    assert state.attributes["friendly_name"] == "Frankfurt (Main) Hauptbahnhof"