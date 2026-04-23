async def test_compile_hourly_statistics_changing_units_1(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    device_class,
    state_unit,
    state_unit2,
    unit_class,
    mean,
    min,
    max,
) -> None:
    """Test compiling hourly statistics where units change from one hour to the next.

    This tests the case where the recorder cannot convert between the units.
    """
    zero = get_start_time(dt_util.utcnow())
    await async_setup_component(hass, "sensor", {})
    # Wait for the sensor recorder platform to be added
    await async_recorder_block_till_done(hass)
    attributes = {
        "device_class": device_class,
        "state_class": "measurement",
        "unit_of_measurement": state_unit,
    }
    with freeze_time(zero) as freezer:
        four, states = await async_record_states(
            hass, freezer, zero, "sensor.test1", attributes
        )
        attributes["unit_of_measurement"] = state_unit2
        four, _states = await async_record_states(
            hass, freezer, zero + timedelta(minutes=5), "sensor.test1", attributes
        )
        states["sensor.test1"] += _states["sensor.test1"]
        four, _states = await async_record_states(
            hass, freezer, zero + timedelta(minutes=10), "sensor.test1", attributes
        )
        states["sensor.test1"] += _states["sensor.test1"]
    await async_wait_recording_done(hass)
    hist = history.get_significant_states(
        hass, zero, four, hass.states.async_entity_ids()
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)

    do_adhoc_statistics(hass, start=zero)
    await async_wait_recording_done(hass)
    assert "cannot be converted to the unit of previously" not in caplog.text
    statistic_ids = await async_list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "statistic_id": "sensor.test1",
            "display_unit_of_measurement": state_unit,
            "has_mean": True,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": state_unit,
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

    do_adhoc_statistics(hass, start=zero + timedelta(minutes=10))
    await async_wait_recording_done(hass)
    assert (
        f"The unit of sensor.test1 ({state_unit2}) cannot be converted to the unit of "
        f"previously compiled statistics ({state_unit})" in caplog.text
    )
    statistic_ids = await async_list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "statistic_id": "sensor.test1",
            "display_unit_of_measurement": state_unit,
            "has_mean": True,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": state_unit,
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
    assert "Error while processing event StatisticsTask" not in caplog.text