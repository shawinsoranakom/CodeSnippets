async def test_raise_for_blocking_call_async_integration_non_strict(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test raise_for_blocking_call detects when called from event loop from integration context."""
    stack = [
        Mock(
            filename="/home/paulus/homeassistant/core.py",
            lineno="15",
            line="do_something()",
        ),
        Mock(
            filename="/home/paulus/homeassistant/components/hue/light.py",
            lineno="15",
            line="self.light.is_on",
        ),
        Mock(
            filename="/home/paulus/aiohue/lights.py",
            lineno="1",
            line="something()",
        ),
    ]
    with patch_get_current_frame(stack):
        haloop.raise_for_blocking_call(banned_function, strict=False)

    assert (
        "Detected blocking call to banned_function with args None"
        " inside the event loop by integration"
        " 'hue' at homeassistant/components/hue/light.py, line 15: self.light.is_on "
        "(offender: /home/paulus/aiohue/lights.py, line 1: mock_line), "
        "please create a bug report at https://github.com/home-assistant/core/issues?"
        "q=is%3Aopen+is%3Aissue+label%3A%22integration%3A+hue%22" in caplog.text
    )
    assert "Traceback (most recent call last)" in caplog.text
    assert (
        'File "/home/paulus/homeassistant/components/hue/light.py", line 15'
        in caplog.text
    )
    assert (
        "please create a bug report at https://github.com/home-assistant/core/issues"
        in caplog.text
    )
    assert (
        "For developers, please see "
        "https://developers.home-assistant.io/docs/asyncio_blocking_operations/#banned_function"
    ) in caplog.text
    warnings = [
        record for record in caplog.get_records("call") if record.levelname == "WARNING"
    ]
    assert len(warnings) == 1
    caplog.clear()

    # Second call should log at debug
    with patch_get_current_frame(stack):
        haloop.raise_for_blocking_call(banned_function, strict=False)

    warnings = [
        record for record in caplog.get_records("call") if record.levelname == "WARNING"
    ]
    assert len(warnings) == 0
    assert (
        "For developers, please see "
        "https://developers.home-assistant.io/docs/asyncio_blocking_operations/#banned_function"
    ) in caplog.text
    # no expensive traceback on debug
    assert "Traceback (most recent call last)" not in caplog.text