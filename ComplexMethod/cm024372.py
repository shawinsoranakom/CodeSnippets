async def test_compile_hourly_statistics_changing_device_class_1(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    device_class,
    unit_1,
    unit_2,
    unit_3,
    unit_class_1,
    unit_class_2,
    factor_2,
    factor_3,
    mean1,
    mean2,
    min,
    max,
) -> None:
    """Test compiling hourly statistics where device class changes from one hour to the next.

    In this test, the device class is first None, then set to a specific device class.

    Changing device class may influence the unit class.
    """
    zero = get_start_time(dt_util.utcnow())
    await async_setup_component(hass, "sensor", {})
    # Wait for the sensor recorder platform to be added
    await async_recorder_block_till_done(hass)

    # Record some states for an initial period, the entity has no device class
    attributes = {
        "state_class": "measurement",
        "unit_of_measurement": unit_1,
    }
    with freeze_time(zero) as freezer:
        four, states = await async_record_states(
            hass, freezer, zero, "sensor.test1", attributes
        )
    await async_wait_recording_done(hass)

    do_adhoc_statistics(hass, start=zero)
    await async_wait_recording_done(hass)
    assert "does not match the unit of already compiled" not in caplog.text
    statistic_ids = await async_list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "statistic_id": "sensor.test1",
            "display_unit_of_measurement": unit_1,
            "has_mean": True,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": unit_1,
            "unit_class": unit_class_1,
        },
    ]
    stats = statistics_during_period(hass, zero, period="5minute")
    assert stats == {
        "sensor.test1": [
            {
                "start": process_timestamp(zero).timestamp(),
                "end": process_timestamp(zero + timedelta(minutes=5)).timestamp(),
                "mean": pytest.approx(mean1),
                "min": pytest.approx(min),
                "max": pytest.approx(max),
                "last_reset": None,
                "state": None,
                "sum": None,
            }
        ]
    }

    # Update device class and record additional states in a different UoM
    attributes["device_class"] = device_class
    attributes["unit_of_measurement"] = unit_2
    seq = [x * factor_2 for x in (-10, 15, 30)]
    with freeze_time(zero) as freezer:
        four, _states = await async_record_states(
            hass, freezer, zero + timedelta(minutes=5), "sensor.test1", attributes, seq
        )
        states["sensor.test1"] += _states["sensor.test1"]
        four, _states = await async_record_states(
            hass, freezer, zero + timedelta(minutes=10), "sensor.test1", attributes, seq
        )
    await async_wait_recording_done(hass)
    states["sensor.test1"] += _states["sensor.test1"]
    hist = history.get_significant_states(
        hass, zero, four, hass.states.async_entity_ids()
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)

    # Run statistics again, additional statistics is generated
    do_adhoc_statistics(hass, start=zero + timedelta(minutes=10))
    await async_wait_recording_done(hass)
    statistic_ids = await async_list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "statistic_id": "sensor.test1",
            "display_unit_of_measurement": unit_2,
            "has_mean": True,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": unit_1,
            "unit_class": unit_class_2,
        },
    ]
    stats = statistics_during_period(hass, zero, period="5minute")
    assert stats == {
        "sensor.test1": [
            {
                "start": process_timestamp(zero).timestamp(),
                "end": process_timestamp(zero + timedelta(minutes=5)).timestamp(),
                "mean": pytest.approx(mean1 * factor_2),
                "min": pytest.approx(min * factor_2),
                "max": pytest.approx(max * factor_2),
                "last_reset": None,
                "state": None,
                "sum": None,
            },
            {
                "start": process_timestamp(zero + timedelta(minutes=10)).timestamp(),
                "end": process_timestamp(zero + timedelta(minutes=15)).timestamp(),
                "mean": pytest.approx(mean2 * factor_2),
                "min": pytest.approx(min * factor_2),
                "max": pytest.approx(max * factor_2),
                "last_reset": None,
                "state": None,
                "sum": None,
            },
        ]
    }

    # Update device class and record additional states in a different UoM
    attributes["unit_of_measurement"] = unit_3
    seq = [x * factor_3 for x in (-10, 15, 30)]
    with freeze_time(zero) as freezer:
        four, _states = await async_record_states(
            hass, freezer, zero + timedelta(minutes=15), "sensor.test1", attributes, seq
        )
        states["sensor.test1"] += _states["sensor.test1"]
        four, _states = await async_record_states(
            hass, freezer, zero + timedelta(minutes=20), "sensor.test1", attributes, seq
        )
    await async_wait_recording_done(hass)
    states["sensor.test1"] += _states["sensor.test1"]
    hist = history.get_significant_states(
        hass, zero, four, hass.states.async_entity_ids()
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)

    # Run statistics again, additional statistics is generated
    do_adhoc_statistics(hass, start=zero + timedelta(minutes=20))
    await async_wait_recording_done(hass)
    statistic_ids = await async_list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "statistic_id": "sensor.test1",
            "display_unit_of_measurement": unit_3,
            "has_mean": True,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": unit_1,
            "unit_class": unit_class_2,
        },
    ]
    stats = statistics_during_period(hass, zero, period="5minute")
    assert stats == {
        "sensor.test1": [
            {
                "start": process_timestamp(zero).timestamp(),
                "end": process_timestamp(zero + timedelta(minutes=5)).timestamp(),
                "mean": pytest.approx(mean1 * factor_3),
                "min": pytest.approx(min * factor_3),
                "max": pytest.approx(max * factor_3),
                "last_reset": None,
                "state": None,
                "sum": None,
            },
            {
                "start": process_timestamp(zero + timedelta(minutes=10)).timestamp(),
                "end": process_timestamp(zero + timedelta(minutes=15)).timestamp(),
                "mean": pytest.approx(mean2 * factor_3),
                "min": pytest.approx(min * factor_3),
                "max": pytest.approx(max * factor_3),
                "last_reset": None,
                "state": None,
                "sum": None,
            },
            {
                "start": process_timestamp(zero + timedelta(minutes=20)).timestamp(),
                "end": process_timestamp(zero + timedelta(minutes=25)).timestamp(),
                "mean": pytest.approx(mean2 * factor_3),
                "min": pytest.approx(min * factor_3),
                "max": pytest.approx(max * factor_3),
                "last_reset": None,
                "state": None,
                "sum": None,
            },
        ]
    }
    assert "Error while processing event StatisticsTask" not in caplog.text