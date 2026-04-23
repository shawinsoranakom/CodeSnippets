async def test_compile_hourly_sum_statistics_amount_reset_every_state_change(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    state_class,
    device_class,
    state_unit,
    display_unit,
    statistics_unit,
    unit_class,
    factor,
) -> None:
    """Test compiling hourly statistics."""
    zero = get_start_time(dt_util.utcnow())
    await async_setup_component(hass, "sensor", {})
    # Wait for the sensor recorder platform to be added
    await async_recorder_block_till_done(hass)
    attributes = {
        "device_class": device_class,
        "state_class": state_class,
        "unit_of_measurement": state_unit,
        "last_reset": None,
    }
    seq = [10, 15, 15, 15, 20, 20, 20, 25]
    # Make sure the sequence has consecutive equal states
    assert seq[1] == seq[2] == seq[3]

    # Make sure the first and last state differ
    assert seq[0] != seq[-1]

    states = {"sensor.test1": []}
    with freeze_time(zero) as freezer:
        # Insert states for a 1st statistics period
        one = zero
        for i in range(len(seq)):
            one = one + timedelta(seconds=5)
            attributes = dict(attributes)
            attributes["last_reset"] = dt_util.as_local(one).isoformat()
            _states = await async_record_meter_state(
                hass, freezer, one, "sensor.test1", attributes, seq[i : i + 1]
            )
            states["sensor.test1"].extend(_states["sensor.test1"])

        # Insert states for a 2nd statistics period
        two = zero + timedelta(minutes=5)
        for i in range(len(seq)):
            two = two + timedelta(seconds=5)
            attributes = dict(attributes)
            attributes["last_reset"] = dt_util.as_local(two).isoformat()
            _states = await async_record_meter_state(
                hass, freezer, two, "sensor.test1", attributes, seq[i : i + 1]
            )
            states["sensor.test1"].extend(_states["sensor.test1"])
    await async_wait_recording_done(hass)

    hist = history.get_significant_states(
        hass,
        zero - timedelta.resolution,
        two + timedelta.resolution,
        hass.states.async_entity_ids(),
        significant_changes_only=False,
    )
    assert_multiple_states_equal_without_context_and_last_changed(
        dict(states)["sensor.test1"], dict(hist)["sensor.test1"]
    )

    do_adhoc_statistics(hass, start=zero)
    do_adhoc_statistics(hass, start=zero + timedelta(minutes=5))
    await async_wait_recording_done(hass)
    statistic_ids = await async_list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "statistic_id": "sensor.test1",
            "display_unit_of_measurement": display_unit,
            "has_mean": False,
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": statistics_unit,
            "unit_class": unit_class,
        }
    ]
    stats = statistics_during_period(hass, zero, period="5minute")
    assert stats == {
        "sensor.test1": [
            {
                "start": process_timestamp(zero).timestamp(),
                "end": process_timestamp(zero + timedelta(minutes=5)).timestamp(),
                "max": None,
                "mean": None,
                "min": None,
                "last_reset": process_timestamp(dt_util.as_local(one)).timestamp(),
                "state": pytest.approx(factor * seq[7]),
                "sum": pytest.approx(factor * (sum(seq) - seq[0])),
            },
            {
                "start": process_timestamp(zero + timedelta(minutes=5)).timestamp(),
                "end": process_timestamp(zero + timedelta(minutes=10)).timestamp(),
                "max": None,
                "mean": None,
                "min": None,
                "last_reset": process_timestamp(dt_util.as_local(two)).timestamp(),
                "state": pytest.approx(factor * seq[7]),
                "sum": pytest.approx(factor * (2 * sum(seq) - seq[0])),
            },
        ]
    }
    assert "Error while processing event StatisticsTask" not in caplog.text