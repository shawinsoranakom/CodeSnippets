async def test_rmvtransport_dest_config(hass: HomeAssistant) -> None:
    """Test destination configuration."""
    with patch(
        "RMVtransport.RMVtransport.get_departures",
        return_value=get_departures_mock(),
    ):
        assert await async_setup_component(hass, "sensor", VALID_CONFIG_DEST)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.frankfurt_main_hauptbahnhof")
    assert state is not None
    assert state.state == "16"
    assert (
        state.attributes["direction"] == "Frankfurt (Main) Hugo-Junkers-Straße/Schleife"
    )
    assert state.attributes["line"] == 12
    assert state.attributes["minutes"] == 16
    assert state.attributes["departure_time"] == datetime.datetime(2018, 8, 6, 14, 30)