async def test_at_start_when_running_callback(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test at start when already running."""
    assert hass.state is CoreState.running
    assert hass.is_running

    calls = []

    @callback
    def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    start.async_at_start(hass, cb_at_start)()
    assert len(calls) == 1

    hass.set_state(CoreState.starting)
    assert hass.is_running

    start.async_at_start(hass, cb_at_start)()
    assert len(calls) == 2

    # Check the unnecessary cancel did not generate warnings or errors
    for record in caplog.records:
        assert record.levelname in ("DEBUG", "INFO")