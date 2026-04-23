async def test_does_not_work_into_the_future(
    recorder_mock: Recorder, hass: HomeAssistant
) -> None:
    """Test history cannot tell the future.

    Verifies we do not regress https://github.com/home-assistant/core/pull/20589
    """
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

    with patch(
        "homeassistant.components.recorder.history.state_changes_during_period",
        _fake_states,
    ):
        with freeze_time(start_time):
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
                            "start": "{{ utcnow().replace(hour=23, minute=0, second=0) }}",
                            "duration": {"hours": 1},
                            "type": "time",
                        },
                        {
                            "platform": "history_stats",
                            "entity_id": "binary_sensor.state",
                            "name": "sensor2",
                            "state": "on",
                            "start": "{{ utcnow().replace(hour=23, minute=0, second=0) }}",
                            "duration": {"hours": 1},
                            "type": "time",
                            "unique_id": "6b1f54e3-4065-43ca-8492-d0d4506a573a",
                        },
                    ]
                },
            )

            await async_update_entity(hass, "sensor.sensor1")
            await hass.async_block_till_done()

        assert hass.states.get("sensor.sensor1").state == STATE_UNKNOWN
        assert hass.states.get("sensor.sensor2").state == STATE_UNKNOWN

        one_hour_in = start_time + timedelta(minutes=60)
        with freeze_time(one_hour_in):
            async_fire_time_changed(hass, one_hour_in)
            await hass.async_block_till_done(wait_background_tasks=True)

        assert hass.states.get("sensor.sensor1").state == STATE_UNKNOWN
        assert hass.states.get("sensor.sensor2").state == STATE_UNKNOWN

        turn_off_time = start_time + timedelta(minutes=90)
        with freeze_time(turn_off_time):
            hass.states.async_set("binary_sensor.state", "off")
            await hass.async_block_till_done()
            async_fire_time_changed(hass, turn_off_time)
            await hass.async_block_till_done(wait_background_tasks=True)

        assert hass.states.get("sensor.sensor1").state == STATE_UNKNOWN
        assert hass.states.get("sensor.sensor2").state == STATE_UNKNOWN

        turn_back_on_time = start_time + timedelta(minutes=105)
        with freeze_time(turn_back_on_time):
            async_fire_time_changed(hass, turn_back_on_time)
            await hass.async_block_till_done(wait_background_tasks=True)

        assert hass.states.get("sensor.sensor1").state == STATE_UNKNOWN
        assert hass.states.get("sensor.sensor2").state == STATE_UNKNOWN

        with freeze_time(turn_back_on_time):
            hass.states.async_set("binary_sensor.state", "on")
            await hass.async_block_till_done()

        assert hass.states.get("sensor.sensor1").state == STATE_UNKNOWN
        assert hass.states.get("sensor.sensor2").state == STATE_UNKNOWN

        end_time = start_time + timedelta(minutes=120)
        with freeze_time(end_time):
            async_fire_time_changed(hass, end_time)
            await hass.async_block_till_done(wait_background_tasks=True)

        assert hass.states.get("sensor.sensor1").state == STATE_UNKNOWN
        assert hass.states.get("sensor.sensor2").state == STATE_UNKNOWN

        in_the_window = start_time + timedelta(hours=23, minutes=5)
        with freeze_time(in_the_window):
            async_fire_time_changed(hass, in_the_window)
            await hass.async_block_till_done(wait_background_tasks=True)

        assert hass.states.get("sensor.sensor1").state == "0.08"
        assert hass.states.get("sensor.sensor2").state == "0.0833333333333333"

    past_the_window = start_time + timedelta(hours=25)
    with (
        patch(
            "homeassistant.components.recorder.history.state_changes_during_period",
            return_value=[],
        ),
        freeze_time(past_the_window),
    ):
        async_fire_time_changed(hass, past_the_window)
        await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get("sensor.sensor1").state == STATE_UNKNOWN

    def _fake_off_states(*args, **kwargs):
        return {
            "binary_sensor.state": [
                ha.State(
                    "binary_sensor.state",
                    "off",
                    last_changed=start_time,
                    last_updated=start_time,
                ),
            ]
        }

    past_the_window_with_data = start_time + timedelta(hours=26)
    with (
        patch(
            "homeassistant.components.recorder.history.state_changes_during_period",
            _fake_off_states,
        ),
        freeze_time(past_the_window_with_data),
    ):
        async_fire_time_changed(hass, past_the_window_with_data)
        await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get("sensor.sensor1").state == STATE_UNKNOWN

    at_the_next_window_with_data = start_time + timedelta(days=1, hours=23)
    with (
        patch(
            "homeassistant.components.recorder.history.state_changes_during_period",
            _fake_off_states,
        ),
        freeze_time(at_the_next_window_with_data),
    ):
        async_fire_time_changed(hass, at_the_next_window_with_data)
        await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get("sensor.sensor1").state == "0.0"