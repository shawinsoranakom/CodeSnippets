async def test_raise_for_blocking_call_async_non_strict_core(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test non_strict_core raise_for_blocking_call detects from event loop without integration context."""
    stack = [
        Mock(
            filename="/home/paulus/homeassistant/core.py",
            lineno="12",
            line="do_something()",
        ),
        Mock(
            filename="/home/paulus/homeassistant/core.py",
            lineno="12",
            line="self.light.is_on",
        ),
        Mock(
            filename="/home/paulus/aiohue/lights.py",
            lineno="2",
            line="something()",
        ),
    ]
    with patch_get_current_frame(stack):
        haloop.raise_for_blocking_call(banned_function, strict_core=False)
    assert "Detected blocking call to banned_function" in caplog.text
    assert "Traceback (most recent call last)" in caplog.text
    assert (
        "Please create a bug report at https://github.com/home-assistant/core/issues"
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
        haloop.raise_for_blocking_call(banned_function, strict_core=False)

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