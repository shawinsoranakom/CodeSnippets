async def test_measure_multiple(recorder_mock: Recorder, hass: HomeAssistant) -> None:
    """Test the history statistics sensor measure for multiple ."""
    start_time = dt_util.utcnow() - timedelta(minutes=60)
    t0 = start_time + timedelta(minutes=20)
    t1 = t0 + timedelta(minutes=10)
    t2 = t1 + timedelta(minutes=10)

    # Start     t0        t1        t2        End
    # |--20min--|--20min--|--10min--|--10min--|
    # |---------|--orange-|-default-|---blue--|

    def _fake_states(*args, **kwargs):
        return {
            "input_select.test_id": [
                # Because we use include_start_time_state we need to mock
                # value at start
                ha.State("input_select.test_id", "", last_changed=start_time),
                ha.State("input_select.test_id", "orange", last_changed=t0),
                ha.State("input_select.test_id", "default", last_changed=t1),
                ha.State("input_select.test_id", "blue", last_changed=t2),
            ]
        }

    with patch(
        "homeassistant.components.recorder.history.state_changes_during_period",
        _fake_states,
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
                        "start": "{{ as_timestamp(utcnow()) - 3600 }}",
                        "end": "{{ utcnow() }}",
                        "type": "time",
                        "state_class": "measurement",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "unknown.test_id",
                        "name": "sensor2",
                        "state": ["orange", "blue"],
                        "start": "{{ as_timestamp(utcnow()) - 3600 }}",
                        "end": "{{ utcnow() }}",
                        "type": "time",
                        "state_class": "total_increasing",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "input_select.test_id",
                        "name": "sensor3",
                        "state": ["orange", "blue"],
                        "start": "{{ as_timestamp(utcnow()) - 3600 }}",
                        "end": "{{ utcnow() }}",
                        "type": "count",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "input_select.test_id",
                        "name": "sensor4",
                        "state": ["orange", "blue"],
                        "start": "{{ as_timestamp(utcnow()) - 3600 }}",
                        "end": "{{ utcnow() }}",
                        "type": "ratio",
                    },
                ]
            },
        )
        await hass.async_block_till_done()
        for i in range(1, 5):
            await async_update_entity(hass, f"sensor.sensor{i}")
        await hass.async_block_till_done()

    assert round(float(hass.states.get("sensor.sensor1").state), 3) == 0.5
    assert hass.states.get("sensor.sensor2").state == "0.0"
    assert hass.states.get("sensor.sensor3").state == "2"
    assert hass.states.get("sensor.sensor4").state == "50.0"

    assert (
        hass.states.get("sensor.sensor1").attributes.get("state_class") == "measurement"
    )
    assert (
        hass.states.get("sensor.sensor2").attributes.get("state_class")
        == "total_increasing"
    )
    assert (
        hass.states.get("sensor.sensor3").attributes.get("state_class") == "measurement"
    )
    assert (
        hass.states.get("sensor.sensor4").attributes.get("state_class") == "measurement"
    )