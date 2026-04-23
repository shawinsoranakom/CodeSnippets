async def test_measure_sliding_window(
    recorder_mock: Recorder, hass: HomeAssistant
) -> None:
    """Test the history statistics sensor with a moving end and a moving start."""
    start_time = dt_util.utcnow() - timedelta(minutes=60)
    t0 = start_time + timedelta(minutes=20)
    t1 = t0 + timedelta(minutes=10)
    t2 = t1 + timedelta(minutes=10)

    # Start     t0        t1        t2        End
    # |--20min--|--20min--|--10min--|--10min--|
    # |---off---|---on----|---off---|---on----|

    def _fake_states(*args, **kwargs):
        return {
            "binary_sensor.test_id": [
                ha.State("binary_sensor.test_id", "on", last_changed=t0),
                ha.State("binary_sensor.test_id", "off", last_changed=t1),
                ha.State("binary_sensor.test_id", "on", last_changed=t2),
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
                        "entity_id": "binary_sensor.test_id",
                        "name": "sensor1",
                        "state": "on",
                        "start": "{{ as_timestamp(now()) - 3600 }}",
                        "end": "{{ as_timestamp(now()) + 3600 }}",
                        "type": "time",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.test_id",
                        "name": "sensor2",
                        "state": "on",
                        "start": "{{ as_timestamp(now()) - 3600 }}",
                        "end": "{{ as_timestamp(now()) + 3600 }}",
                        "type": "time",
                        "unique_id": "6b1f54e3-4065-43ca-8492-d0d4506a573a",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.test_id",
                        "name": "sensor3",
                        "state": "on",
                        "start": "{{ as_timestamp(now()) - 3600 }}",
                        "end": "{{ as_timestamp(now()) + 3600 }}",
                        "type": "count",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.test_id",
                        "name": "sensor4",
                        "state": "on",
                        "start": "{{ as_timestamp(now()) - 3600 }}",
                        "end": "{{ as_timestamp(now()) + 3600 }}",
                        "type": "ratio",
                    },
                ]
            },
        )
        await hass.async_block_till_done()
        for i in range(1, 5):
            await async_update_entity(hass, f"sensor.sensor{i}")
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "0.0"
    assert float(hass.states.get("sensor.sensor2").state) == 0
    assert hass.states.get("sensor.sensor3").state == "0"
    assert hass.states.get("sensor.sensor4").state == "0.0"

    past_next_update = start_time + timedelta(minutes=30)
    with (
        patch(
            "homeassistant.components.recorder.history.state_changes_during_period",
            _fake_states,
        ),
        freeze_time(past_next_update),
    ):
        async_fire_time_changed(hass, past_next_update)
        await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get("sensor.sensor1").state == "0.17"
    assert 0.166 < float(hass.states.get("sensor.sensor2").state) < 0.167
    assert hass.states.get("sensor.sensor3").state == "1"
    assert hass.states.get("sensor.sensor4").state == "8.3"