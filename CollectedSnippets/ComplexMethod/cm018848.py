async def test_multi_jail(hass: HomeAssistant) -> None:
    """Test that log is parsed correctly when using multiple jails."""
    log_parser = BanLogParser("/test/fail2ban.log")
    sensor1 = BanSensor("fail2ban", "jail_one", log_parser)
    sensor2 = BanSensor("fail2ban", "jail_two", log_parser)
    sensor1.hass = hass
    sensor2.hass = hass
    assert sensor1.name == "fail2ban jail_one"
    assert sensor2.name == "fail2ban jail_two"
    mock_fh = mock_open(read_data=fake_log("multi_jail"))
    with patch("homeassistant.components.fail2ban.sensor.open", mock_fh, create=True):
        sensor1.update()
        sensor2.update()

    assert sensor1.state == "111.111.111.111"
    assert sensor1.extra_state_attributes[STATE_CURRENT_BANS] == ["111.111.111.111"]
    assert sensor1.extra_state_attributes[STATE_ALL_BANS] == ["111.111.111.111"]
    assert sensor2.state == "222.222.222.222"
    assert sensor2.extra_state_attributes[STATE_CURRENT_BANS] == ["222.222.222.222"]
    assert sensor2.extra_state_attributes[STATE_ALL_BANS] == ["222.222.222.222"]