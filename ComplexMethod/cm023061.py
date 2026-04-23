async def test_coordinator_setup_and_update_errors(
    hass: HomeAssistant,
    load_config_entry: tuple[MockConfigEntry, Mock],
    get_data: YaleSmartAlarmData,
) -> None:
    """Test the Yale Smart Living coordinator with errors."""

    client = load_config_entry[1]

    state = hass.states.get("alarm_control_panel.test_username")
    assert state.state == AlarmControlPanelState.ARMED_AWAY
    client.reset_mock()

    client.get_information.side_effect = ConnectionError("Could not connect")
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=1))
    await hass.async_block_till_done(wait_background_tasks=True)
    client.get_information.assert_called_once()
    state = hass.states.get("alarm_control_panel.test_username")
    assert state.state == STATE_UNAVAILABLE
    client.reset_mock()

    client.get_information.side_effect = ConnectionError("Could not connect")
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=2))
    await hass.async_block_till_done(wait_background_tasks=True)
    client.get_information.assert_called_once()
    state = hass.states.get("alarm_control_panel.test_username")
    assert state.state == STATE_UNAVAILABLE
    client.reset_mock()

    client.get_information.side_effect = TimeoutError("Could not connect")
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=3))
    await hass.async_block_till_done(wait_background_tasks=True)
    client.get_information.assert_called_once()
    state = hass.states.get("alarm_control_panel.test_username")
    assert state.state == STATE_UNAVAILABLE
    client.reset_mock()

    client.get_information.side_effect = UnknownError("info")
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=4))
    await hass.async_block_till_done(wait_background_tasks=True)
    client.get_information.assert_called_once()
    state = hass.states.get("alarm_control_panel.test_username")
    assert state.state == STATE_UNAVAILABLE
    client.reset_mock()

    client.get_information.side_effect = None
    client.get_information.return_value = get_data
    client.get_armed_status.return_value = YALE_STATE_ARM_FULL
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)
    client.get_information.assert_called_once()
    state = hass.states.get("alarm_control_panel.test_username")
    assert state.state == AlarmControlPanelState.ARMED_AWAY
    client.reset_mock()

    client.get_information.side_effect = AuthenticationError("Can not authenticate")
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=6))
    await hass.async_block_till_done(wait_background_tasks=True)
    client.get_information.assert_called_once()
    state = hass.states.get("alarm_control_panel.test_username")
    assert state.state == STATE_UNAVAILABLE