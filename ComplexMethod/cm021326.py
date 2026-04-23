async def test_async_around_min_state_duration(
    recorder_mock: Recorder,
    hass: HomeAssistant,
) -> None:
    """Test min_state_duration boundary where block becomes valid."""
    await hass.config.async_set_time_zone("UTC")
    utcnow = dt_util.utcnow()
    start_time = utcnow.replace(hour=0, minute=0, second=0, microsecond=0)
    t0 = start_time + timedelta(minutes=9)
    t1 = start_time + timedelta(minutes=10)
    t2 = start_time + timedelta(minutes=11)

    # Start     t0        t1        t2        End
    # |---9min--|---1min--|---1min--|---1min--|
    # |---on----|---on----|---on----|---on----|

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
                        "duration": {"hours": 1},
                        "min_state_duration": {"minutes": 10},
                        "type": "time",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.state",
                        "name": "sensor2",
                        "state": "on",
                        "start": "{{ utcnow().replace(hour=0, minute=0, second=0) }}",
                        "duration": {"hours": 1},
                        "min_state_duration": {"minutes": 10},
                        "type": "count",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.state",
                        "name": "sensor3",
                        "state": "on",
                        "start": "{{ utcnow().replace(hour=0, minute=0, second=0) }}",
                        "duration": {"hours": 1},
                        "min_state_duration": {"minutes": 10},
                        "type": "ratio",
                    },
                ]
            },
        )
        await hass.async_block_till_done()

        for i in range(1, 4):
            await async_update_entity(hass, f"sensor.sensor{i}")
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "0.0"
    assert hass.states.get("sensor.sensor2").state == "0"
    assert hass.states.get("sensor.sensor3").state == "0.0"

    with freeze_time(t0):
        async_fire_time_changed(hass, t0)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "0.0"
    assert hass.states.get("sensor.sensor2").state == "0"
    assert hass.states.get("sensor.sensor3").state == "0.0"

    with freeze_time(t1):
        async_fire_time_changed(hass, t1)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "0.17"
    assert hass.states.get("sensor.sensor2").state == "1"
    assert hass.states.get("sensor.sensor3").state == "16.7"

    with freeze_time(t2):
        async_fire_time_changed(hass, t2)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "0.18"
    assert hass.states.get("sensor.sensor2").state == "1"
    assert hass.states.get("sensor.sensor3").state == "18.3"