async def test_immediate_works_with_schedule_call(hass: HomeAssistant) -> None:
    """Test immediate works with scheduled calls."""
    calls = []
    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=True,
        function=AsyncMock(side_effect=lambda: calls.append(None)),
    )

    # Call when nothing happening
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert debouncer._timer_task is not None
    assert debouncer._execute_at_end_of_timer is False
    assert debouncer._job.target == debouncer.function

    # Call when cooldown active setting execute at end to True
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert debouncer._timer_task is not None
    assert debouncer._execute_at_end_of_timer is True
    assert debouncer._job.target == debouncer.function

    # Canceling debounce in cooldown
    debouncer.async_cancel()
    assert debouncer._timer_task is None
    assert debouncer._execute_at_end_of_timer is False
    assert debouncer._job.target == debouncer.function

    before_job = debouncer._job

    # Call and let timer run out
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    assert len(calls) == 2
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    assert len(calls) == 2
    assert debouncer._timer_task is None
    assert debouncer._execute_at_end_of_timer is False
    assert debouncer._job.target == debouncer.function
    assert debouncer._job == before_job

    # Test calling enabled timer if currently executing.
    await debouncer._execute_lock.acquire()
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    assert len(calls) == 2
    assert debouncer._timer_task is not None
    assert debouncer._execute_at_end_of_timer is True
    debouncer._execute_lock.release()
    assert debouncer._job.target == debouncer.function

    debouncer.async_shutdown()