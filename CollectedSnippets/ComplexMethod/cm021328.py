async def test_measure_multiple_with_min_state_duration(
    recorder_mock: Recorder, hass: HomeAssistant
) -> None:
    """Test measure for multiple states with min state duration."""
    start_time = dt_util.utcnow() - timedelta(minutes=40)
    t0 = start_time + timedelta(minutes=10)
    t1 = t0 + timedelta(minutes=10)
    t2 = t1 + timedelta(minutes=10)

    # Start     t0        t1        t2        End
    # |--10min--|--10min--|--10min--|--10min--|
    # |---blue--|--orange-|-default-|---blue--|

    def _fake_states(*args, **kwargs):
        return {
            "input_select.test_id": [
                ha.State(
                    "input_select.test_id",
                    "blue",
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
                        "entity_id": "input_select.test_id",
                        "name": "sensor1",
                        "state": ["orange", "blue"],
                        "duration": {"hours": 1},
                        "end": "{{ utcnow() }}",
                        "min_state_duration": {"minutes": 15},
                        "type": "time",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "input_select.test_id",
                        "name": "sensor2",
                        "state": ["orange", "blue"],
                        "duration": {"hours": 1},
                        "end": "{{ utcnow() }}",
                        "min_state_duration": {"minutes": 15},
                        "type": "count",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "input_select.test_id",
                        "name": "sensor3",
                        "state": ["orange", "blue"],
                        "duration": {"hours": 1},
                        "end": "{{ utcnow() }}",
                        "min_state_duration": {"minutes": 15},
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
        hass.states.async_set("input_select.test_id", "orange")
        await hass.async_block_till_done()
        async_fire_time_changed(hass, t0)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "0.0"
    assert hass.states.get("sensor.sensor2").state == "0"
    assert hass.states.get("sensor.sensor3").state == "0.0"

    with freeze_time(t1):
        hass.states.async_set("input_select.test_id", "blue")
        await hass.async_block_till_done()
        async_fire_time_changed(hass, t1)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "0.33"
    assert hass.states.get("sensor.sensor2").state == "1"
    assert hass.states.get("sensor.sensor3").state == "33.3"

    with freeze_time(t2):
        hass.states.async_set("input_select.test_id", "blue")
        await hass.async_block_till_done()
        async_fire_time_changed(hass, t2)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "0.5"
    assert hass.states.get("sensor.sensor2").state == "1"
    assert hass.states.get("sensor.sensor3").state == "50.0"