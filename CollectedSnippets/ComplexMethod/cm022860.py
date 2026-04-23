async def test_sensor(
    hass: HomeAssistant,
    tankerkoenig: AsyncMock,
    config_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the tankerkoenig sensors."""

    state = hass.states.get("sensor.station_somewhere_street_1_super_e10")
    assert state
    assert state.state == "1.659"
    assert state.attributes == snapshot

    state = hass.states.get("sensor.station_somewhere_street_1_super")
    assert state
    assert state.state == "1.719"
    assert state.attributes == snapshot

    state = hass.states.get("sensor.station_somewhere_street_1_diesel")
    assert state
    assert state.state == "1.659"
    assert state.attributes == snapshot