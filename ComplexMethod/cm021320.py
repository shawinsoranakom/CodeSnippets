async def test_start_from_history_then_watch_state_changes_sliding(
    recorder_mock: Recorder,
    hass: HomeAssistant,
) -> None:
    """Test we startup from history and switch to watching state changes.

    With a sliding window, history_stats does not requery the recorder.
    """
    await hass.config.async_set_time_zone("UTC")
    utcnow = dt_util.utcnow()
    start_time = utcnow.replace(hour=0, minute=0, second=0, microsecond=0)
    time = start_time

    def _fake_states(*args, **kwargs):
        return {
            "binary_sensor.state": [
                ha.State(
                    "binary_sensor.state",
                    "off",
                    last_changed=start_time - timedelta(hours=1),
                    last_updated=start_time - timedelta(hours=1),
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
                        "name": f"sensor{i}",
                        "state": "on",
                        "end": "{{ utcnow() }}",
                        "duration": {"hours": 1},
                        "type": sensor_type,
                    }
                    for i, sensor_type in enumerate(["time", "ratio", "count"])
                ]
                + [
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.state",
                        "name": f"sensor_delayed{i}",
                        "state": "on",
                        "end": "{{ utcnow()-timedelta(minutes=5) }}",
                        "duration": {"minutes": 55},
                        "type": sensor_type,
                    }
                    for i, sensor_type in enumerate(["time", "ratio", "count"])
                ]
            },
        )
        await hass.async_block_till_done()

        for i in range(3):
            await async_update_entity(hass, f"sensor.sensor{i}")
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor0").state == "0.0"
    assert hass.states.get("sensor.sensor1").state == "0.0"
    assert hass.states.get("sensor.sensor2").state == "0"
    assert hass.states.get("sensor.sensor_delayed0").state == "0.0"
    assert hass.states.get("sensor.sensor_delayed1").state == "0.0"
    assert hass.states.get("sensor.sensor_delayed2").state == "0"

    with freeze_time(time):
        hass.states.async_set("binary_sensor.state", "on")
        await hass.async_block_till_done()
        async_fire_time_changed(hass, time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor0").state == "0.0"
    assert hass.states.get("sensor.sensor1").state == "0.0"
    assert hass.states.get("sensor.sensor2").state == "1"
    # Delayed sensor will not have registered the turn on yet
    assert hass.states.get("sensor.sensor_delayed0").state == "0.0"
    assert hass.states.get("sensor.sensor_delayed1").state == "0.0"
    assert hass.states.get("sensor.sensor_delayed2").state == "0"

    # After sensor has been on for 15 minutes, check state
    time += timedelta(minutes=15)  # 00:15
    with freeze_time(time):
        async_fire_time_changed(hass, time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor0").state == "0.25"
    assert hass.states.get("sensor.sensor1").state == "25.0"
    assert hass.states.get("sensor.sensor2").state == "1"
    # Delayed sensor will only have data from 00:00 - 00:10
    assert hass.states.get("sensor.sensor_delayed0").state == "0.17"
    assert hass.states.get("sensor.sensor_delayed1").state == "18.2"  # 10 / 55
    assert hass.states.get("sensor.sensor_delayed2").state == "1"

    with freeze_time(time):
        hass.states.async_set("binary_sensor.state", "off")
        await hass.async_block_till_done()
        async_fire_time_changed(hass, time)
        await hass.async_block_till_done()

    time += timedelta(minutes=30)  # 00:45

    with freeze_time(time):
        async_fire_time_changed(hass, time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor0").state == "0.25"
    assert hass.states.get("sensor.sensor1").state == "25.0"
    assert hass.states.get("sensor.sensor2").state == "1"
    assert hass.states.get("sensor.sensor_delayed0").state == "0.25"
    assert hass.states.get("sensor.sensor_delayed1").state == "27.3"  # 15 / 55
    assert hass.states.get("sensor.sensor_delayed2").state == "1"

    time += timedelta(minutes=20)  # 01:05

    with freeze_time(time):
        async_fire_time_changed(hass, time)
        await hass.async_block_till_done()

    # Sliding window will have started to erase the initial on period, so now it will only be on for 10 minutes
    assert hass.states.get("sensor.sensor0").state == "0.17"
    assert hass.states.get("sensor.sensor1").state == "16.7"
    assert hass.states.get("sensor.sensor2").state == "1"
    assert hass.states.get("sensor.sensor_delayed0").state == "0.17"
    assert hass.states.get("sensor.sensor_delayed1").state == "18.2"  # 10 / 55
    assert hass.states.get("sensor.sensor_delayed2").state == "1"

    time += timedelta(minutes=5)  # 01:10

    with freeze_time(time):
        async_fire_time_changed(hass, time)
        await hass.async_block_till_done()

    # Sliding window will continue to erase the initial on period, so now it will only be on for 5 minutes
    assert hass.states.get("sensor.sensor0").state == "0.08"
    assert hass.states.get("sensor.sensor1").state == "8.3"
    assert hass.states.get("sensor.sensor2").state == "1"
    assert hass.states.get("sensor.sensor_delayed0").state == "0.08"
    assert hass.states.get("sensor.sensor_delayed1").state == "9.1"  # 5 / 55
    assert hass.states.get("sensor.sensor_delayed2").state == "1"

    time += timedelta(minutes=10)  # 01:20

    with freeze_time(time):
        async_fire_time_changed(hass, time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor0").state == "0.0"
    assert hass.states.get("sensor.sensor1").state == "0.0"
    assert hass.states.get("sensor.sensor2").state == "0"
    assert hass.states.get("sensor.sensor_delayed0").state == "0.0"
    assert hass.states.get("sensor.sensor_delayed1").state == "0.0"
    assert hass.states.get("sensor.sensor_delayed2").state == "0"