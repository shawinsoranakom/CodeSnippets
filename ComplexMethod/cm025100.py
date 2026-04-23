def test_timedelta(mock_is_safe, hass: HomeAssistant) -> None:
    """Test relative_time method."""
    now = datetime.strptime("2000-01-01 10:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
    with freeze_time(now):
        result = render(hass, "{{timedelta(seconds=120)}}")
        assert result == "0:02:00"

        result = render(hass, "{{timedelta(seconds=86400)}}")
        assert result == "1 day, 0:00:00"

        result = render(hass, "{{timedelta(days=1, hours=4)}}")
        assert result == "1 day, 4:00:00"

        result = render(hass, "{{relative_time(now() - timedelta(seconds=3600))}}")
        assert result == "1 hour"

        result = render(hass, "{{relative_time(now() - timedelta(seconds=86400))}}")
        assert result == "1 day"

        result = render(hass, "{{relative_time(now() - timedelta(seconds=86401))}}")
        assert result == "1 day"

        result = render(hass, "{{relative_time(now() - timedelta(weeks=2, days=1))}}")
        assert result == "15 days"