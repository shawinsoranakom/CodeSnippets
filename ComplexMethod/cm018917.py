async def test_streaming(
    hass: HomeAssistant, twitch_mock: AsyncMock, config_entry: MockConfigEntry
) -> None:
    """Test streaming state."""
    await setup_integration(hass, config_entry)

    sensor_state = hass.states.get(ENTITY_ID)
    assert sensor_state.state == "streaming"
    assert sensor_state.attributes["entity_picture"] == "stream-medium.png"
    assert sensor_state.attributes["channel_picture"] == "logo.png"
    assert sensor_state.attributes["game"] == "Good game"
    assert sensor_state.attributes["title"] == "Title"
    assert sensor_state.attributes["started_at"] == datetime(
        year=2021, month=3, day=10, hour=3, minute=18, second=11, tzinfo=tzutc()
    )
    assert sensor_state.attributes["viewers"] == 42