async def test_compile_hourly_statistics_convert_units_1(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    device_class,
    state_unit_1,
    state_unit_2,
    unit_class,
    mean,
    min,
    max,
    factor,
) -> None:
    """Test compiling hourly statistics where units change from one hour to the next.

    This tests the case where the recorder can convert between the units.
    """
    zero = get_start_time(dt_util.utcnow())
    await async_setup_component(hass, "sensor", {})
    # Wait for the sensor recorder platform to be added
    await async_recorder_block_till_done(hass)
    attributes = {
        "device_class": device_class,
        "state_class": "measurement",
        "unit_of_measurement": state_unit_1,
    }
    with freeze_time(zero) as freezer:
        four, states = await async_record_states(
            hass, freezer, zero, "sensor.test1", attributes
        )
        four, _states = await async_record_states(
            hass,
            freezer,
            zero + timedelta(minutes=5),
            "sensor.test1",
            attributes,
            seq=[0, 1, None],
        )
    await async_wait_recording_done(hass)
    states["sensor.test1"] += _states["sensor.test1"]

    do_adhoc_statistics(hass, start=zero)
    await async_wait_recording_done(hass)
    assert "does not match the unit of already compiled" not in caplog.text
    statistic_ids = await async_list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "statistic_id": "sensor.test1",
            "display_unit_of_measurement": state_unit_1,
            "has_mean": True,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": state_unit_1,
            "unit_class": unit_class,
        },
    ]
    stats = statistics_during_period(hass, zero, period="5minute")
    assert stats == {
        "sensor.test1": [
            {
                "start": process_timestamp(zero).timestamp(),
                "end": process_timestamp(zero + timedelta(minutes=5)).timestamp(),
                "mean": pytest.approx(mean),
                "min": pytest.approx(min),
                "max": pytest.approx(max),
                "last_reset": None,
                "state": None,
                "sum": None,
            }
        ]
    }

    attributes["unit_of_measurement"] = state_unit_2
    with freeze_time(four) as freezer:
        four, _states = await async_record_states(
            hass, freezer, zero + timedelta(minutes=10), "sensor.test1", attributes
        )
    await async_wait_recording_done(hass)
    states["sensor.test1"] += _states["sensor.test1"]
    hist = history.get_significant_states(
        hass, zero, four, hass.states.async_entity_ids()
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)
    do_adhoc_statistics(hass, start=zero + timedelta(minutes=10))
    await async_wait_recording_done(hass)
    assert "The unit of sensor.test1 is changing" not in caplog.text
    assert (
        f"matches the unit of already compiled statistics ({state_unit_1})"
        not in caplog.text
    )
    statistic_ids = await async_list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "statistic_id": "sensor.test1",
            "display_unit_of_measurement": state_unit_2,
            "has_mean": True,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": state_unit_1,
            "unit_class": unit_class,
        },
    ]
    stats = statistics_during_period(hass, zero, period="5minute")
    assert stats == {
        "sensor.test1": [
            {
                "start": process_timestamp(zero).timestamp(),
                "end": process_timestamp(zero + timedelta(minutes=5)).timestamp(),
                "mean": pytest.approx(mean * factor),
                "min": pytest.approx(min * factor),
                "max": pytest.approx(max * factor),
                "last_reset": None,
                "state": None,
                "sum": None,
            },
            {
                "start": process_timestamp(zero + timedelta(minutes=10)).timestamp(),
                "end": process_timestamp(zero + timedelta(minutes=15)).timestamp(),
                "mean": pytest.approx(mean),
                "min": pytest.approx(min),
                "max": pytest.approx(max),
                "last_reset": None,
                "state": None,
                "sum": None,
            },
        ]
    }
    assert "Error while processing event StatisticsTask" not in caplog.text