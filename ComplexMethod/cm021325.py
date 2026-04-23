async def test_end_time_with_microseconds_zeroed(
    time_zone: str,
    async_setup_recorder_instance: RecorderInstanceGenerator,
    hass: HomeAssistant,
) -> None:
    """Test the history statistics sensor that has the end time microseconds zeroed out."""
    await hass.config.async_set_time_zone(time_zone)
    start_of_today = dt_util.now().replace(
        day=9, month=7, year=1986, hour=0, minute=0, second=0, microsecond=0
    )
    with freeze_time(start_of_today):
        await async_setup_recorder_instance(hass)
        await hass.async_block_till_done()
        await async_wait_recording_done(hass)

    start_time = start_of_today + timedelta(minutes=60)
    t0 = start_time + timedelta(minutes=20)
    t1 = t0 + timedelta(minutes=10)
    t2 = t1 + timedelta(minutes=10)
    time_200 = start_of_today + timedelta(hours=2)

    def _fake_states(*args, **kwargs):
        return {
            "binary_sensor.heatpump_compressor_state": [
                ha.State(
                    "binary_sensor.heatpump_compressor_state", "on", last_changed=t0
                ),
                ha.State(
                    "binary_sensor.heatpump_compressor_state",
                    "off",
                    last_changed=t1,
                ),
                ha.State(
                    "binary_sensor.heatpump_compressor_state", "on", last_changed=t2
                ),
            ]
        }

    with (
        freeze_time(time_200),
        patch(
            "homeassistant.components.recorder.history.state_changes_during_period",
            _fake_states,
        ),
    ):
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.heatpump_compressor_state",
                        "name": "heatpump_compressor_today",
                        "state": "on",
                        "start": "{{ now().replace(hour=0, minute=0, second=0, microsecond=0) }}",
                        "end": "{{ now().replace(microsecond=0) }}",
                        "type": "time",
                    },
                    {
                        "platform": "history_stats",
                        "entity_id": "binary_sensor.heatpump_compressor_state",
                        "name": "heatpump_compressor_today2",
                        "state": "on",
                        "start": "{{ now().replace(hour=0, minute=0, second=0, microsecond=0) }}",
                        "end": "{{ now().replace(microsecond=0) }}",
                        "type": "time",
                        "unique_id": "6b1f54e3-4065-43ca-8492-d0d4506a573a",
                    },
                ]
            },
        )
        await hass.async_block_till_done()
        await async_update_entity(hass, "sensor.heatpump_compressor_today")
        await hass.async_block_till_done()
        assert hass.states.get("sensor.heatpump_compressor_today").state == "0.5"
        assert (
            0.499
            < float(hass.states.get("sensor.heatpump_compressor_today2").state)
            < 0.501
        )

        async_fire_time_changed(hass, time_200)
        assert hass.states.get("sensor.heatpump_compressor_today").state == "0.5"
        assert (
            0.499
            < float(hass.states.get("sensor.heatpump_compressor_today2").state)
            < 0.501
        )
        hass.states.async_set("binary_sensor.heatpump_compressor_state", "off")
        await hass.async_block_till_done()

    time_400 = start_of_today + timedelta(hours=4)
    with freeze_time(time_400):
        async_fire_time_changed(hass, time_400)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert hass.states.get("sensor.heatpump_compressor_today").state == "0.5"
        assert (
            0.499
            < float(hass.states.get("sensor.heatpump_compressor_today2").state)
            < 0.501
        )
        hass.states.async_set("binary_sensor.heatpump_compressor_state", "on")
        await async_wait_recording_done(hass)
    time_600 = start_of_today + timedelta(hours=6)
    with freeze_time(time_600):
        async_fire_time_changed(hass, time_600)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert hass.states.get("sensor.heatpump_compressor_today").state == "2.5"
        assert (
            2.499
            < float(hass.states.get("sensor.heatpump_compressor_today2").state)
            < 2.501
        )

    rolled_to_next_day = start_of_today + timedelta(days=1)
    assert rolled_to_next_day.hour == 0
    assert rolled_to_next_day.minute == 0
    assert rolled_to_next_day.second == 0
    assert rolled_to_next_day.microsecond == 0

    with freeze_time(rolled_to_next_day):
        async_fire_time_changed(hass, rolled_to_next_day)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert hass.states.get("sensor.heatpump_compressor_today").state == "0.0"
        assert hass.states.get("sensor.heatpump_compressor_today2").state == "0.0"

    rolled_to_next_day_plus_12 = start_of_today + timedelta(
        days=1, hours=12, microseconds=0
    )
    with freeze_time(rolled_to_next_day_plus_12):
        async_fire_time_changed(hass, rolled_to_next_day_plus_12)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert hass.states.get("sensor.heatpump_compressor_today").state == "12.0"
        assert hass.states.get("sensor.heatpump_compressor_today2").state == "12.0"

    rolled_to_next_day_plus_14 = start_of_today + timedelta(
        days=1, hours=14, microseconds=0
    )
    with freeze_time(rolled_to_next_day_plus_14):
        async_fire_time_changed(hass, rolled_to_next_day_plus_14)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert hass.states.get("sensor.heatpump_compressor_today").state == "14.0"
        assert hass.states.get("sensor.heatpump_compressor_today2").state == "14.0"

    rolled_to_next_day_plus_16_860000 = start_of_today + timedelta(
        days=1, hours=16, microseconds=860000
    )
    with freeze_time(rolled_to_next_day_plus_16_860000):
        hass.states.async_set("binary_sensor.heatpump_compressor_state", "off")
        await async_wait_recording_done(hass)
        async_fire_time_changed(hass, rolled_to_next_day_plus_16_860000)
        await hass.async_block_till_done(wait_background_tasks=True)

    rolled_to_next_day_plus_18 = start_of_today + timedelta(days=1, hours=18)
    with freeze_time(rolled_to_next_day_plus_18):
        async_fire_time_changed(hass, rolled_to_next_day_plus_18)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert hass.states.get("sensor.heatpump_compressor_today").state == "16.0"
        assert (
            hass.states.get("sensor.heatpump_compressor_today2").state
            == "16.0002388888929"
        )