async def test_periodic_task_leaving_dst_2(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test periodic task behavior when leaving dst."""
    await hass.config.async_set_time_zone("Europe/Vienna")
    specific_runs = []

    today = date.today().isoformat()

    # Make sure we leave DST during the test
    now_local = dt_util.now()
    assert now_local.utcoffset() != (now_local + timedelta(hours=1)).utcoffset()

    unsub = async_track_time_change(
        hass,
        # pylint: disable-next=unnecessary-lambda
        callback(lambda x: specific_runs.append(x)),
        minute=30,
        second=0,
    )

    # The task should not fire yet
    freezer.move_to(f"{today} 02:28:00.999999+02:00")
    async_fire_time_changed(hass)
    assert dt_util.now().fold == 0
    await hass.async_block_till_done()
    assert len(specific_runs) == 0

    # The task should fire
    freezer.move_to(f"{today} 02:55:00.999999+02:00")
    async_fire_time_changed(hass)
    assert dt_util.now().fold == 0
    await hass.async_block_till_done()
    assert len(specific_runs) == 1

    # DST has ended, the task should not fire yet
    freezer.move_to(f"{today} 02:15:00.999999+01:00")
    async_fire_time_changed(hass)
    assert dt_util.now().fold == 1
    await hass.async_block_till_done()
    assert len(specific_runs) == 1

    # The task should fire
    freezer.move_to(f"{today} 02:45:00.999999+01:00")
    async_fire_time_changed(hass)
    assert dt_util.now().fold == 1
    await hass.async_block_till_done()
    assert len(specific_runs) == 2

    # The task should not fire again
    freezer.move_to(f"{today} 02:55:00.999999+01:00")
    async_fire_time_changed(hass)
    assert dt_util.now().fold == 1
    await hass.async_block_till_done()
    assert len(specific_runs) == 2

    # The task should fire again the next hour
    freezer.move_to(f"{today} 03:55:00.999999+01:00")
    async_fire_time_changed(hass)
    assert dt_util.now().fold == 0
    await hass.async_block_till_done()
    assert len(specific_runs) == 3

    unsub()