async def test_player_alarm_sensors_state(
    hass: HomeAssistant,
    mock_player: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test player alarm binary sensors with default states."""

    player = mock_player

    # Test alarm upcoming sensor
    upcoming_state = hass.states.get("binary_sensor.alarm_upcoming")
    assert upcoming_state is not None
    assert upcoming_state.state == STATE_ON

    # Test alarm active sensor
    active_state = hass.states.get("binary_sensor.alarm_active")
    assert active_state is not None
    assert active_state.state == STATE_OFF

    # Test alarm snooze sensor
    snooze_state = hass.states.get("binary_sensor.alarm_snoozed")
    assert snooze_state is not None
    assert snooze_state.state == STATE_OFF

    # Toggle alarm states and verify sensors update
    player.alarm_upcoming = False
    player.alarm_active = True
    player.alarm_snooze = True
    freezer.tick(timedelta(seconds=PLAYER_UPDATE_INTERVAL))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    upcoming_state = hass.states.get("binary_sensor.alarm_upcoming")
    assert upcoming_state is not None
    assert upcoming_state.state == STATE_OFF

    active_state = hass.states.get("binary_sensor.alarm_active")
    assert active_state is not None
    assert active_state.state == STATE_ON