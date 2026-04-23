async def test_not_immediate_works_schedule_call(hass: HomeAssistant) -> None:
    """Test immediate works with schedule call."""
    calls = []
    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=False,
        function=AsyncMock(side_effect=lambda: calls.append(None)),
    )

    # Call when nothing happening
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    assert len(calls) == 0
    assert debouncer._timer_task is not None
    assert debouncer._execute_at_end_of_timer is True

    # Call while still on cooldown
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    assert len(calls) == 0
    assert debouncer._timer_task is not None
    assert debouncer._execute_at_end_of_timer is True

    # Canceling while on cooldown
    debouncer.async_cancel()
    assert debouncer._timer_task is None
    assert debouncer._execute_at_end_of_timer is False

    # Call and let timer run out
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert debouncer._timer_task is not None
    assert debouncer._execute_at_end_of_timer is False
    assert debouncer._job.target == debouncer.function

    # Reset debouncer
    debouncer.async_cancel()

    # Test calling enabled timer if currently executing.
    await debouncer._execute_lock.acquire()
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert debouncer._timer_task is not None
    assert debouncer._execute_at_end_of_timer is True
    debouncer._execute_lock.release()
    assert debouncer._job.target == debouncer.function

    debouncer.async_shutdown()