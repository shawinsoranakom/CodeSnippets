async def test_statistics_duplicated(
    hass: HomeAssistant, setup_recorder: None, caplog: pytest.LogCaptureFixture
) -> None:
    """Test statistics with same start time is not compiled."""
    await async_setup_component(hass, "sensor", {})
    zero, four, states = await async_record_states(hass)
    hist = history.get_significant_states(hass, zero, four, list(states))
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)

    await async_wait_recording_done(hass)
    assert "Compiling statistics for" not in caplog.text
    assert "Statistics already compiled" not in caplog.text

    with patch(
        "homeassistant.components.sensor.recorder.compile_statistics",
        return_value=statistics.PlatformCompiledStatistics([], {}),
    ) as compile_statistics:
        do_adhoc_statistics(hass, start=zero)
        await async_wait_recording_done(hass)
        assert compile_statistics.called
        compile_statistics.reset_mock()
        assert "Compiling statistics for" in caplog.text
        assert "Statistics already compiled" not in caplog.text
        caplog.clear()

        do_adhoc_statistics(hass, start=zero)
        await async_wait_recording_done(hass)
        assert not compile_statistics.called
        compile_statistics.reset_mock()
        assert "Compiling statistics for" not in caplog.text
        assert "Statistics already compiled" in caplog.text
        caplog.clear()