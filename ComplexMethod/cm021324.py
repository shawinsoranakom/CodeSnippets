async def test_state_change_during_window_rollover(
    recorder_mock: Recorder,
    hass: HomeAssistant,
) -> None:
    """Test when the tracked sensor and the start/end window change during the same update."""
    await hass.config.async_set_time_zone("UTC")
    utcnow = dt_util.utcnow()
    start_time = utcnow.replace(hour=23, minute=0, second=0, microsecond=0)

    def _fake_states(*args, **kwargs):
        return {
            "binary_sensor.state": [
                ha.State(
                    "binary_sensor.state",
                    "on",
                    last_changed=start_time - timedelta(hours=11),
                    last_updated=start_time - timedelta(hours=11),
                ),
            ]
        }

    # The test begins at 23:00, and queries from the database that the sensor has been on since 12:00.
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
                        "start": "{{ today_at('12:00') if now().hour == 1 else today_at() }}",
                        "end": "{{ now() }}",
                        "type": "time",
                    }
                ]
            },
        )
        await hass.async_block_till_done()

        await async_update_entity(hass, "sensor.sensor1")
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "11.0"

    # Advance 59 minutes, to record the last minute update just before midnight, just like a real system would do.
    t2 = start_time + timedelta(minutes=59, microseconds=300)  # 23:59
    with freeze_time(t2):
        async_fire_time_changed(hass, t2)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "11.98"

    # One minute has passed and the time has now rolled over into a new day, resetting the recorder window.
    # The sensor will be ON since midnight.
    t3 = t2 + timedelta(minutes=1)  # 00:01
    with freeze_time(t3):
        # The sensor turns off around this time, before the sensor does its normal polled update.
        hass.states.async_set("binary_sensor.state", "off")
        await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get("sensor.sensor1").state == "0.0"

    # More time passes, and the history stats does a polled update again. It should be 0 since the sensor has been off since midnight.
    # Turn the sensor back on.
    t4 = t3 + timedelta(minutes=10)  # 00:10
    with freeze_time(t4):
        async_fire_time_changed(hass, t4)
        await hass.async_block_till_done()
        hass.states.async_set("binary_sensor.state", "on")
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "0.0"

    # Due to time change, start time has now moved into the future. Turn off the sensor.
    t5 = t4 + timedelta(hours=1)  # 01:10
    with freeze_time(t5):
        hass.states.async_set("binary_sensor.state", "off")
        await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get("sensor.sensor1").state == STATE_UNKNOWN

    # Start time has moved back to start of today. Turn the sensor on at the same time it is recomputed
    # Should query the recorder this time due to start time moving backwards in time.
    t6 = t5 + timedelta(hours=1)  # 02:10

    def _fake_states_t6(*args, **kwargs):
        return {
            "binary_sensor.state": [
                ha.State(
                    "binary_sensor.state",
                    "off",
                    last_changed=t6.replace(hour=0, minute=0, second=0, microsecond=0),
                ),
                ha.State(
                    "binary_sensor.state",
                    "on",
                    last_changed=t6.replace(hour=0, minute=10, second=0, microsecond=0),
                ),
                ha.State(
                    "binary_sensor.state",
                    "off",
                    last_changed=t6.replace(hour=1, minute=10, second=0, microsecond=0),
                ),
            ]
        }

    with (
        patch(
            "homeassistant.components.recorder.history.state_changes_during_period",
            _fake_states_t6,
        ),
        freeze_time(t6),
    ):
        hass.states.async_set("binary_sensor.state", "on")
        await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get("sensor.sensor1").state == "1.0"

    # Another hour passes since the re-query. Total 'On' time should be 2 hours (00:10-1:10, 2:10-now (3:10))
    t7 = t6 + timedelta(hours=1)  # 03:10
    with freeze_time(t7):
        async_fire_time_changed(hass, t7)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "2.0"