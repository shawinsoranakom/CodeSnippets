async def test_async_start_from_history_and_switch_to_watching_state_changes_multiple(
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
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.state",
                        "name": "sensor2",
                        "state": "on",
                        "start": "{{ utcnow().replace(hour=0, minute=0, second=0) }}",
                        "duration": {"hours": 2},
                        "type": "time",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.state",
                        "name": "sensor3",
                        "state": "on",
                        "start": "{{ utcnow().replace(hour=0, minute=0, second=0) }}",
                        "duration": {"hours": 2},
                        "type": "count",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.state",
                        "name": "sensor4",
                        "state": "on",
                        "start": "{{ utcnow().replace(hour=0, minute=0, second=0) }}",
                        "duration": {"hours": 2},
                        "type": "ratio",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.state",
                        "name": "sensor5",
                        "state": "on",
                        "start": "{{ utcnow().replace(hour=0, minute=0, second=0) }}",
                        "duration": {"hours": 2},
                        "min_state_duration": {"minutes": 5},
                        "type": "time",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.state",
                        "name": "sensor6",
                        "state": "off",
                        "start": "{{ utcnow().replace(hour=0, minute=0, second=0) }}",
                        "duration": {"hours": 2},
                        "min_state_duration": {"minutes": 20},
                        "type": "time",
                    },
                ]
            },
        )
        await hass.async_block_till_done()

        for i in range(1, 5):
            await async_update_entity(hass, f"sensor.sensor{i}")
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "0.0"
    assert hass.states.get("sensor.sensor2").state == "0.0"
    assert hass.states.get("sensor.sensor3").state == "1"
    assert hass.states.get("sensor.sensor4").state == "0.0"
    assert hass.states.get("sensor.sensor5").state == "0.0"
    assert hass.states.get("sensor.sensor6").state == "0.0"

    one_hour_in = start_time + timedelta(minutes=60)
    with freeze_time(one_hour_in):
        async_fire_time_changed(hass, one_hour_in)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "1.0"
    assert hass.states.get("sensor.sensor2").state == "1.0"
    assert hass.states.get("sensor.sensor3").state == "1"
    assert hass.states.get("sensor.sensor4").state == "50.0"
    assert hass.states.get("sensor.sensor5").state == "1.0"
    assert hass.states.get("sensor.sensor6").state == "0.0"

    turn_off_time = start_time + timedelta(minutes=90)
    with freeze_time(turn_off_time):
        hass.states.async_set("binary_sensor.state", "off")
        await hass.async_block_till_done()
        async_fire_time_changed(hass, turn_off_time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "1.5"
    assert hass.states.get("sensor.sensor2").state == "1.5"
    assert hass.states.get("sensor.sensor3").state == "1"
    assert hass.states.get("sensor.sensor4").state == "75.0"
    assert hass.states.get("sensor.sensor5").state == "1.5"
    assert hass.states.get("sensor.sensor6").state == "0.0"

    turn_back_on_time = start_time + timedelta(minutes=105)
    with freeze_time(turn_back_on_time):
        async_fire_time_changed(hass, turn_back_on_time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "1.5"
    assert hass.states.get("sensor.sensor2").state == "1.5"
    assert hass.states.get("sensor.sensor3").state == "1"
    assert hass.states.get("sensor.sensor4").state == "75.0"
    assert hass.states.get("sensor.sensor5").state == "1.5"
    assert hass.states.get("sensor.sensor6").state == "0.0"

    with freeze_time(turn_back_on_time):
        hass.states.async_set("binary_sensor.state", "on")
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "1.5"
    assert hass.states.get("sensor.sensor2").state == "1.5"
    assert hass.states.get("sensor.sensor3").state == "2"
    assert hass.states.get("sensor.sensor4").state == "75.0"
    assert hass.states.get("sensor.sensor5").state == "1.5"
    assert hass.states.get("sensor.sensor6").state == "0.0"

    end_time = start_time + timedelta(minutes=120)
    with freeze_time(end_time):
        async_fire_time_changed(hass, end_time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == "1.75"
    assert hass.states.get("sensor.sensor2").state == "1.75"
    assert hass.states.get("sensor.sensor3").state == "2"
    assert hass.states.get("sensor.sensor4").state == "87.5"
    assert hass.states.get("sensor.sensor5").state == "1.75"
    assert hass.states.get("sensor.sensor6").state == "0.0"