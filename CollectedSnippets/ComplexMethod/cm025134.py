async def test_time_since(mock_is_safe, hass: HomeAssistant) -> None:
    """Test time_since method."""
    await hass.config.async_set_time_zone("UTC")
    now = datetime.strptime("2000-01-01 10:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
    time_since_template = (
        '{{time_since(strptime("2000-01-01 09:00:00", "%Y-%m-%d %H:%M:%S"))}}'
    )
    with freeze_time(now):
        result = render(hass, time_since_template)
        assert result == "1 hour"

        result = render(
            hass,
            (
                "{{"
                "  time_since("
                "    strptime("
                '        "2000-01-01 09:00:00 +01:00",'
                '        "%Y-%m-%d %H:%M:%S %z"'
                "    )"
                "  )"
                "}}"
            ),
        )
        assert result == "2 hours"

        result = render(
            hass,
            (
                "{{"
                "  time_since("
                "    strptime("
                '       "2000-01-01 03:00:00 -06:00",'
                '       "%Y-%m-%d %H:%M:%S %z"'
                "    )"
                "  )"
                "}}"
            ),
        )
        assert result == "1 hour"

        result1 = str(
            datetime.strptime("2000-01-01 11:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
        )
        result2 = render(
            hass,
            (
                "{{"
                "  time_since("
                "    strptime("
                '       "2000-01-01 11:00:00 +00:00",'
                '       "%Y-%m-%d %H:%M:%S %z"),'
                "    precision = 2"
                "  )"
                "}}"
            ),
        )
        assert result1 == result2

        result = render(
            hass,
            (
                "{{"
                "  time_since("
                "    strptime("
                '        "2000-01-01 09:05:00 +01:00",'
                '        "%Y-%m-%d %H:%M:%S %z"),'
                "       precision=2"
                "  )"
                "}}"
            ),
        )
        assert result == "1 hour 55 minutes"

        result = render(
            hass,
            (
                "{{"
                "  time_since("
                "    strptime("
                '       "2000-01-01 02:05:27 -06:00",'
                '       "%Y-%m-%d %H:%M:%S %z"),'
                "       precision = 3"
                "  )"
                "}}"
            ),
        )
        assert result == "1 hour 54 minutes 33 seconds"
        result = render(
            hass,
            (
                "{{"
                "  time_since("
                "    strptime("
                '       "2000-01-01 02:05:27 -06:00",'
                '       "%Y-%m-%d %H:%M:%S %z")'
                "  )"
                "}}"
            ),
        )
        assert result == "2 hours"
        result = render(
            hass,
            (
                "{{"
                "  time_since("
                "    strptime("
                '       "1999-02-01 02:05:27 -06:00",'
                '       "%Y-%m-%d %H:%M:%S %z"),'
                "       precision = 0"
                "  )"
                "}}"
            ),
        )
        assert result == "11 months 4 days 1 hour 54 minutes 33 seconds"
        result = render(
            hass,
            (
                "{{"
                "  time_since("
                "    strptime("
                '       "1999-02-01 02:05:27 -06:00",'
                '       "%Y-%m-%d %H:%M:%S %z")'
                "  )"
                "}}"
            ),
        )
        assert result == "11 months"
        result1 = str(
            datetime.strptime("2000-01-01 11:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
        )
        result2 = render(
            hass,
            (
                "{{"
                "  time_since("
                "    strptime("
                '       "2000-01-01 11:00:00 +00:00",'
                '       "%Y-%m-%d %H:%M:%S %z"),'
                "       precision=3"
                "  )"
                "}}"
            ),
        )
        assert result1 == result2

        result = render(hass, '{{time_since("string")}}')
        assert result == "string"

        info = render_to_info(hass, time_since_template)
        assert info.has_time is True