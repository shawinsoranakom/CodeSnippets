async def test_compile_hourly_sum_statistics_amount(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
    units,
    state_class,
    device_class,
    state_unit,
    display_unit,
    statistics_unit,
    unit_class,
    factor,
) -> None:
    """Test compiling hourly statistics."""
    period0 = get_start_time(dt_util.utcnow())
    period0_end = period1 = period0 + timedelta(minutes=5)
    period1_end = period2 = period0 + timedelta(minutes=10)
    period2_end = period0 + timedelta(minutes=15)
    hass.config.units = units
    await async_setup_component(hass, "sensor", {})
    # Wait for the sensor recorder platform to be added
    await async_recorder_block_till_done(hass)
    attributes = {
        "device_class": device_class,
        "state_class": state_class,
        "unit_of_measurement": state_unit,
        "last_reset": None,
    }
    seq = [10, 15, 20, 10, 30, 40, 50, 60, 70]
    with freeze_time(period0) as freezer:
        four, eight, states = await async_record_meter_states(
            hass, freezer, period0, "sensor.test1", attributes, seq
        )
    await async_wait_recording_done(hass)
    hist = history.get_significant_states(
        hass,
        period0 - timedelta.resolution,
        eight + timedelta.resolution,
        hass.states.async_entity_ids(),
    )
    assert_multiple_states_equal_without_context_and_last_changed(
        dict(states)["sensor.test1"], dict(hist)["sensor.test1"]
    )

    do_adhoc_statistics(hass, start=period0)
    await async_wait_recording_done(hass)
    do_adhoc_statistics(hass, start=period1)
    await async_wait_recording_done(hass)
    do_adhoc_statistics(hass, start=period2)
    await async_wait_recording_done(hass)
    statistic_ids = await async_list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "statistic_id": "sensor.test1",
            "display_unit_of_measurement": statistics_unit,
            "has_mean": False,
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": statistics_unit,
            "unit_class": unit_class,
        }
    ]
    stats = statistics_during_period(hass, period0, period="5minute")
    expected_stats = {
        "sensor.test1": [
            {
                "start": process_timestamp(period0).timestamp(),
                "end": process_timestamp(period0_end).timestamp(),
                "max": None,
                "mean": None,
                "min": None,
                "last_reset": process_timestamp(period0).timestamp(),
                "state": pytest.approx(factor * seq[2]),
                "sum": pytest.approx(factor * 10.0),
            },
            {
                "start": process_timestamp(period1).timestamp(),
                "end": process_timestamp(period1_end).timestamp(),
                "max": None,
                "mean": None,
                "min": None,
                "last_reset": process_timestamp(four).timestamp(),
                "state": pytest.approx(factor * seq[5]),
                "sum": pytest.approx(factor * 40.0),
            },
            {
                "start": process_timestamp(period2).timestamp(),
                "end": process_timestamp(period2_end).timestamp(),
                "max": None,
                "mean": None,
                "min": None,
                "last_reset": process_timestamp(four).timestamp(),
                "state": pytest.approx(factor * seq[8]),
                "sum": pytest.approx(factor * 70.0),
            },
        ]
    }
    assert stats == expected_stats

    # With an offset of 1 minute, we expect to get the 2nd and 3rd periods
    stats = statistics_during_period(
        hass, period0 + timedelta(minutes=1), period="5minute"
    )
    assert stats == {"sensor.test1": expected_stats["sensor.test1"][1:3]}

    # With an offset of 5 minutes, we expect to get the 2nd and 3rd periods
    stats = statistics_during_period(
        hass, period0 + timedelta(minutes=5), period="5minute"
    )
    assert stats == {"sensor.test1": expected_stats["sensor.test1"][1:3]}

    # With an offset of 6 minutes, we expect to get the 3rd period
    stats = statistics_during_period(
        hass, period0 + timedelta(minutes=6), period="5minute"
    )
    assert stats == {"sensor.test1": expected_stats["sensor.test1"][2:3]}

    assert "Error while processing event StatisticsTask" not in caplog.text
    assert "Detected new cycle for sensor.test1, last_reset set to" in caplog.text
    assert "Compiling initial sum statistics for sensor.test1" in caplog.text
    assert "Detected new cycle for sensor.test1, value dropped" not in caplog.text

    client = await hass_ws_client()

    # Adjust the inserted statistics
    await client.send_json(
        {
            "id": 1,
            "type": "recorder/adjust_sum_statistics",
            "statistic_id": "sensor.test1",
            "start_time": period1.isoformat(),
            "adjustment": 100.0,
            "adjustment_unit_of_measurement": display_unit,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    await async_wait_recording_done(hass)

    expected_stats["sensor.test1"][1]["sum"] = pytest.approx(factor * 40.0 + 100)
    expected_stats["sensor.test1"][2]["sum"] = pytest.approx(factor * 70.0 + 100)
    stats = statistics_during_period(hass, period0, period="5minute")
    assert stats == expected_stats

    # Adjust the inserted statistics
    await client.send_json(
        {
            "id": 2,
            "type": "recorder/adjust_sum_statistics",
            "statistic_id": "sensor.test1",
            "start_time": period2.isoformat(),
            "adjustment": -400.0,
            "adjustment_unit_of_measurement": display_unit,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    await async_wait_recording_done(hass)

    expected_stats["sensor.test1"][1]["sum"] = pytest.approx(factor * 40.0 + 100)
    expected_stats["sensor.test1"][2]["sum"] = pytest.approx(factor * 70.0 - 300)
    stats = statistics_during_period(hass, period0, period="5minute")
    assert stats == expected_stats