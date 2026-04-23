def test_update_when_value_changed(
    hass: HomeAssistant, requests_mock: requests_mock.Mocker
) -> None:
    """Test state gets updated when sensor returns a new status."""
    _api, sensor_dict = setup_api(hass, MOCK_DATA_NEXT, requests_mock)
    now = datetime(1970, month=1, day=1)
    with patch("homeassistant.util.dt.now", return_value=now):
        for name, value in sensor_dict.items():
            sensor = value["sensor"]
            fake_delay(hass, 2)
            sensor.update()
            if name == google_wifi.ATTR_LAST_RESTART:
                assert sensor.state == "1969-12-30 00:00:00"
            elif name == google_wifi.ATTR_UPTIME:
                assert sensor.state == 2
            elif name == google_wifi.ATTR_STATUS:
                assert sensor.state == "Offline"
            elif name == google_wifi.ATTR_NEW_VERSION:
                assert sensor.state == "Latest"
            elif name == google_wifi.ATTR_LOCAL_IP:
                assert sensor.state is None
            else:
                assert sensor.state == "next"