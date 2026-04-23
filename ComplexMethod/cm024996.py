async def test_refresh_known_errors_retry_after(
    exc: update_coordinator.UpdateFailed,
    expected_exception: type[Exception],
    message: str,
    crd: update_coordinator.DataUpdateCoordinator[int],
    caplog: pytest.LogCaptureFixture,
    hass: HomeAssistant,
) -> None:
    """Test raising known errors, this time with retry_after."""
    unsub = crd.async_add_listener(lambda: None)

    crd.update_method = AsyncMock(side_effect=exc)

    with (
        patch.object(hass.loop, "time", return_value=1_000.0),
        patch.object(hass.loop, "call_at") as mock_call_at,
    ):
        await crd.async_refresh()

        assert crd.data is None
        assert crd.last_update_success is False
        assert isinstance(crd.last_exception, expected_exception)
        assert message in caplog.text

        when = mock_call_at.call_args[0][0]

        expected = 1_000.0 + crd._microsecond + exc.retry_after
        assert abs(when - expected) < 0.005, (when, expected)

        assert crd._retry_after is None

        # Next schedule should fall back to regular update_interval
        mock_call_at.reset_mock()
        crd._schedule_refresh()
        when2 = mock_call_at.call_args[0][0]
        expected_cancelled = (
            1_000.0 + crd._microsecond + crd.update_interval.total_seconds()
        )
        assert abs(when2 - expected_cancelled) < 0.005, (when2, expected_cancelled)

    unsub()
    crd._unschedule_refresh()