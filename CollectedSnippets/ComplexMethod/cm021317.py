async def test_async_start_from_history_and_switch_to_watching_state_changes_single(
    recorder_mock: Recorder,
    hass: HomeAssistant,
) -> None:
    """Test we startup from history and switch to watching state changes."""
    await hass.config.async_set_time_zone("UTC")
    utcnow = dt_util.utcnow()
    start_time = utcnow.replace(hour=0, minute=0, second=0, microsecond=0)

    # Start     t0        t1        t2       Startup                                       End
    # |--20min--|--20min--|--10min--|--10min--|---------30min---------|---15min--|---15min--|
    # |---on----|---on----|---on----|---on----|----------on-----------|---off----|----on----|

    def _fake_states(*args, **kwargs):
        return {
            "binary_sensor.state": [
                ha.State(
                    "binary_sensor.state",
                    "on",
                    last_changed=start_time,
                    last_updated=start_time,
                ),
            ]
        }

    with (
        patch(
            "homeassistant.components.recorder.history.state_changes_during_period",
            _fake_states,
        ),
        freeze_time(start_time),
    ):
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.state",
                        "name": "sensor1",
                        "state": "on",
                        "start": "{{ utcnow().replace(hour=0, minute=0, second=0) }}",
                        "duration": {"hours": 2},
                        "type": "time",
                    }
                ]
            },
        )
        await hass.async_block_till_done()

        await async_update_entity(hass, "sensor.sensor1")
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "0.0"

    one_hour_in = start_time + timedelta(minutes=60)
    with freeze_time(one_hour_in):
        async_fire_time_changed(hass, one_hour_in)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "1.0"

    turn_off_time = start_time + timedelta(minutes=90)
    with freeze_time(turn_off_time):
        hass.states.async_set("binary_sensor.state", "off")
        await hass.async_block_till_done()
        async_fire_time_changed(hass, turn_off_time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "1.5"

    turn_back_on_time = start_time + timedelta(minutes=105)
    with freeze_time(turn_back_on_time):
        async_fire_time_changed(hass, turn_back_on_time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "1.5"

    with freeze_time(turn_back_on_time):
        hass.states.async_set("binary_sensor.state", "on")
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "1.5"

    end_time = start_time + timedelta(minutes=120)
    with freeze_time(end_time):
        async_fire_time_changed(hass, end_time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "1.75"

    # The window has ended, it should not change again
    after_end_time = start_time + timedelta(minutes=125)
    with freeze_time(after_end_time):
        async_fire_time_changed(hass, after_end_time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "1.75"