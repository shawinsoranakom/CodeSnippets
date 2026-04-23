async def test_time_until(mock_is_safe, hass: HomeAssistant) -> None:
    """Test time_until method."""
    await hass.config.async_set_time_zone("UTC")
    now = datetime.strptime("2000-01-01 10:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
    time_until_template = (
        '{{time_until(strptime("2000-01-01 11:00:00", "%Y-%m-%d %H:%M:%S"))}}'
    )
    with freeze_time(now):
        result = render(hass, time_until_template)
        assert result == "1 hour"

        result = render(
            hass,
            (
                "{{"
                "  time_until("
                "    strptime("
                '        "2000-01-01 13:00:00 +01:00",'
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
                "  time_until("
                "    strptime("
                '       "2000-01-01 05:00:00 -06:00",'
                '       "%Y-%m-%d %H:%M:%S %z"'
                "    )"
                "  )"
                "}}"
            ),
        )
        assert result == "1 hour"

        result1 = str(
            datetime.strptime("2000-01-01 09:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
        )
        result2 = render(
            hass,
            (
                "{{"
                "  time_until("
                "    strptime("
                '       "2000-01-01 09:00:00 +00:00",'
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
                "  time_until("
                "    strptime("
                '        "2000-01-01 12:05:00 +01:00",'
                '        "%Y-%m-%d %H:%M:%S %z"),'
                "       precision=2"
                "  )"
                "}}"
            ),
        )
        assert result == "1 hour 5 minutes"

        result = render(
            hass,
            (
                "{{"
                "  time_until("
                "    strptime("
                '       "2000-01-01 05:54:33 -06:00",'
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
                "  time_until("
                "    strptime("
                '       "2000-01-01 05:54:33 -06:00",'
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
                "  time_until("
                "    strptime("
                '       "2001-02-01 05:54:33 -06:00",'
                '       "%Y-%m-%d %H:%M:%S %z"),'
                "       precision = 0"
                "  )"
                "}}"
            ),
        )
        assert result == "1 year 1 month 2 days 1 hour 54 minutes 33 seconds"
        result = render(
            hass,
            (
                "{{"
                "  time_until("
                "    strptime("
                '       "2001-02-01 05:54:33 -06:00",'
                '       "%Y-%m-%d %H:%M:%S %z"),'
                "       precision = 4"
                "  )"
                "}}"
            ),
        )
        assert result == "1 year 1 month 2 days 2 hours"
        result1 = str(
            datetime.strptime("2000-01-01 09:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
        )
        result2 = render(
            hass,
            (
                "{{"
                "  time_until("
                "    strptime("
                '       "2000-01-01 09:00:00 +00:00",'
                '       "%Y-%m-%d %H:%M:%S %z"),'
                "       precision=3"
                "  )"
                "}}"
            ),
        )
        assert result1 == result2

        result = render(hass, '{{time_until("string")}}')
        assert result == "string"

        info = render_to_info(hass, time_until_template)
        assert info.has_time is True