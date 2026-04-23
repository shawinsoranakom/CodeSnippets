def test_state(hass: HomeAssistant, requests_mock: requests_mock.Mocker) -> None:
    """Test the initial state."""
    _api, sensor_dict = setup_api(hass, MOCK_DATA, requests_mock)
    now = datetime(1970, month=1, day=1)
    with patch("homeassistant.util.dt.now", return_value=now):
        for name, value in sensor_dict.items():
            sensor = value["sensor"]
            fake_delay(hass, 2)
            sensor.update()
            if name == google_wifi.ATTR_LAST_RESTART:
                assert sensor.state == "1969-12-31 00:00:00"
            elif name == google_wifi.ATTR_UPTIME:
                assert sensor.state == 1
            elif name == google_wifi.ATTR_STATUS:
                assert sensor.state == "Online"
            else:
                assert sensor.state == "initial"