async def test_timestamp_custom(hass: HomeAssistant) -> None:
    """Test the timestamps to custom filter."""
    await hass.config.async_set_time_zone("UTC")
    now = dt_util.utcnow()
    tests = [
        (1469119144, None, True, "2016-07-21 16:39:04"),
        (1469119144, "%Y", True, 2016),
        (1469119144, "invalid", True, "invalid"),
        (dt_util.as_timestamp(now), None, False, now.strftime("%Y-%m-%d %H:%M:%S")),
    ]

    for inp, fmt, local, out in tests:
        if fmt:
            fil = f"timestamp_custom('{fmt}')"
        elif fmt and local:
            fil = f"timestamp_custom('{fmt}', {local})"
        else:
            fil = "timestamp_custom"

        assert render(hass, f"{{{{ {inp} | {fil} }}}}") == out

    # Test handling of invalid input
    invalid_tests = [
        (None, None, None),
    ]

    for inp, fmt, local in invalid_tests:
        if fmt:
            fil = f"timestamp_custom('{fmt}')"
        elif fmt and local:
            fil = f"timestamp_custom('{fmt}', {local})"
        else:
            fil = "timestamp_custom"

        with pytest.raises(TemplateError):
            render(hass, f"{{{{ {inp} | {fil} }}}}")

    # Test handling of default return value
    assert render(hass, "{{ None | timestamp_custom('invalid', True, 1) }}") == 1
    assert render(hass, "{{ None | timestamp_custom(default=1) }}") == 1