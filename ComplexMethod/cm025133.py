async def test_relative_time(mock_is_safe, hass: HomeAssistant) -> None:
    """Test relative_time method."""
    await hass.config.async_set_time_zone("UTC")
    now = datetime.strptime("2000-01-01 10:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
    relative_time_template = (
        '{{relative_time(strptime("2000-01-01 09:00:00", "%Y-%m-%d %H:%M:%S"))}}'
    )
    with freeze_time(now):
        result = render(hass, relative_time_template)
        assert result == "1 hour"
        result = render(
            hass,
            (
                "{{"
                "  relative_time("
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
                "  relative_time("
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
                "  relative_time("
                "    strptime("
                '       "2000-01-01 11:00:00 +00:00",'
                '       "%Y-%m-%d %H:%M:%S %z"'
                "    )"
                "  )"
                "}}"
            ),
        )
        assert result1 == result2

        result = render(hass, '{{relative_time("string")}}')
        assert result == "string"

        # Test behavior when current time is same as the input time
        result = render(
            hass,
            (
                "{{"
                "  relative_time("
                "    strptime("
                '        "2000-01-01 10:00:00 +00:00",'
                '        "%Y-%m-%d %H:%M:%S %z"'
                "    )"
                "  )"
                "}}"
            ),
        )
        assert result == "0 seconds"

        # Test behavior when the input time is in the future
        result = render(
            hass,
            (
                "{{"
                "  relative_time("
                "    strptime("
                '        "2000-01-01 11:00:00 +00:00",'
                '        "%Y-%m-%d %H:%M:%S %z"'
                "    )"
                "  )"
                "}}"
            ),
        )
        assert result == "2000-01-01 11:00:00+00:00"

        info = render_to_info(hass, relative_time_template)
        assert info.has_time is True