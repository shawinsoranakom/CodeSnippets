async def test_compile_hourly_statistics(
    hass: HomeAssistant,
    setup_recorder: None,
) -> None:
    """Test compiling hourly statistics."""
    instance = recorder.get_instance(hass)
    await async_setup_component(hass, "sensor", {})
    zero, four, states = await async_record_states(hass)
    hist = history.get_significant_states(hass, zero, four, list(states))
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)

    # Should not fail if there is nothing there yet
    with session_scope(hass=hass, read_only=True) as session:
        stats = get_latest_short_term_statistics_with_session(
            hass,
            session,
            {"sensor.test1", "sensor.wind_direction"},
            {"last_reset", "max", "mean", "min", "state", "sum"},
        )
    assert stats == {}

    for kwargs in ({}, {"statistic_ids": ["sensor.test1", "sensor.wind_direction"]}):
        stats = statistics_during_period(hass, zero, period="5minute", **kwargs)
        assert stats == {}
    for sensor in ("sensor.test1", "sensor.wind_direction"):
        stats = get_last_short_term_statistics(
            hass,
            0,
            sensor,
            True,
            {"last_reset", "max", "mean", "min", "state", "sum"},
        )
        assert stats == {}

    do_adhoc_statistics(hass, start=zero)
    do_adhoc_statistics(hass, start=four)
    await async_wait_recording_done(hass)

    metadata = get_metadata(
        hass, statistic_ids={"sensor.test1", "sensor.test2", "sensor.wind_direction"}
    )
    for sensor, mean_type in (
        ("sensor.test1", StatisticMeanType.ARITHMETIC),
        ("sensor.test2", StatisticMeanType.ARITHMETIC),
        ("sensor.wind_direction", StatisticMeanType.CIRCULAR),
    ):
        assert metadata[sensor][1]["mean_type"] is mean_type
        assert metadata[sensor][1]["has_sum"] is False
    expected_1 = {
        "start": process_timestamp(zero).timestamp(),
        "end": process_timestamp(zero + timedelta(minutes=5)).timestamp(),
        "mean": pytest.approx(14.915254237288135),
        "min": pytest.approx(10.0),
        "max": pytest.approx(20.0),
        "last_reset": None,
    }
    expected_2 = {
        "start": process_timestamp(four).timestamp(),
        "end": process_timestamp(four + timedelta(minutes=5)).timestamp(),
        "mean": pytest.approx(20.0),
        "min": pytest.approx(20.0),
        "max": pytest.approx(20.0),
        "last_reset": None,
    }
    expected_stats1 = [expected_1, expected_2]
    expected_stats2 = [expected_1, expected_2]

    expected_stats_wind_direction1 = {
        "start": process_timestamp(zero).timestamp(),
        "end": process_timestamp(zero + timedelta(minutes=5)).timestamp(),
        "mean": pytest.approx(358.6387003873801),
        "min": None,
        "max": None,
        "last_reset": None,
    }
    expected_stats_wind_direction2 = {
        "start": process_timestamp(four).timestamp(),
        "end": process_timestamp(four + timedelta(minutes=5)).timestamp(),
        "mean": pytest.approx(5),
        "min": None,
        "max": None,
        "last_reset": None,
    }
    expected_stats_wind_direction = [
        expected_stats_wind_direction1,
        expected_stats_wind_direction2,
    ]

    # Test statistics_during_period
    stats = statistics_during_period(
        hass,
        zero,
        period="5minute",
        statistic_ids={"sensor.test1", "sensor.test2", "sensor.wind_direction"},
    )
    assert stats == {
        "sensor.test1": expected_stats1,
        "sensor.test2": expected_stats2,
        "sensor.wind_direction": expected_stats_wind_direction,
    }

    # Test statistics_during_period with a far future start and end date
    future = dt_util.as_utc(dt_util.parse_datetime("2221-11-01 00:00:00"))
    stats = statistics_during_period(
        hass,
        future,
        end_time=future,
        period="5minute",
        statistic_ids={"sensor.test1", "sensor.test2", "sensor.wind_direction"},
    )
    assert stats == {}

    # Test statistics_during_period with a far future end date
    stats = statistics_during_period(
        hass,
        zero,
        end_time=future,
        period="5minute",
        statistic_ids={"sensor.test1", "sensor.test2", "sensor.wind_direction"},
    )
    assert stats == {
        "sensor.test1": expected_stats1,
        "sensor.test2": expected_stats2,
        "sensor.wind_direction": expected_stats_wind_direction,
    }

    stats = statistics_during_period(
        hass, zero, statistic_ids={"sensor.test2"}, period="5minute"
    )
    assert stats == {"sensor.test2": expected_stats2}

    stats = statistics_during_period(
        hass, zero, statistic_ids={"sensor.test3"}, period="5minute"
    )
    assert stats == {}

    # Test get_last_short_term_statistics and get_latest_short_term_statistics
    for sensor, expected in (
        ("sensor.test1", expected_2),
        ("sensor.wind_direction", expected_stats_wind_direction2),
    ):
        stats = get_last_short_term_statistics(
            hass,
            0,
            sensor,
            True,
            {"last_reset", "max", "mean", "min", "state", "sum"},
        )
        assert stats == {}

        stats = get_last_short_term_statistics(
            hass,
            1,
            sensor,
            True,
            {"last_reset", "max", "mean", "min", "state", "sum"},
        )
        assert stats == {sensor: [expected]}

    with session_scope(hass=hass, read_only=True) as session:
        stats = get_latest_short_term_statistics_with_session(
            hass,
            session,
            {"sensor.test1", "sensor.wind_direction"},
            {"last_reset", "max", "mean", "min", "state", "sum"},
        )
    assert stats == {
        "sensor.test1": [expected_2],
        "sensor.wind_direction": [expected_stats_wind_direction2],
    }

    # Now wipe the latest_short_term_statistics_ids table and test again
    # to make sure we can rebuild the missing data
    run_cache = get_short_term_statistics_run_cache(instance.hass)
    run_cache._latest_id_by_metadata_id = {}
    with session_scope(hass=hass, read_only=True) as session:
        stats = get_latest_short_term_statistics_with_session(
            hass,
            session,
            {"sensor.test1", "sensor.wind_direction"},
            {"last_reset", "max", "mean", "min", "state", "sum"},
        )
    assert stats == {
        "sensor.test1": [expected_2],
        "sensor.wind_direction": [expected_stats_wind_direction2],
    }

    metadata = get_metadata(hass, statistic_ids={"sensor.test1"})
    with session_scope(hass=hass, read_only=True) as session:
        stats = get_latest_short_term_statistics_with_session(
            hass,
            session,
            {"sensor.test1"},
            {"last_reset", "max", "mean", "min", "state", "sum"},
            metadata=metadata,
        )
    assert stats == {"sensor.test1": [expected_2]}

    # Test with multiple metadata ids
    metadata = get_metadata(
        hass, statistic_ids={"sensor.test1", "sensor.wind_direction"}
    )
    with session_scope(hass=hass, read_only=True) as session:
        stats = get_latest_short_term_statistics_with_session(
            hass,
            session,
            {"sensor.test1", "sensor.wind_direction"},
            {"last_reset", "max", "mean", "min", "state", "sum"},
            metadata=metadata,
        )
    assert stats == {
        "sensor.test1": [expected_2],
        "sensor.wind_direction": [expected_stats_wind_direction2],
    }

    for sensor, expected in (
        ("sensor.test1", expected_stats1[::-1]),
        ("sensor.wind_direction", expected_stats_wind_direction[::-1]),
    ):
        stats = get_last_short_term_statistics(
            hass,
            2,
            sensor,
            True,
            {"last_reset", "max", "mean", "min", "state", "sum"},
        )
        assert stats == {sensor: expected}

        stats = get_last_short_term_statistics(
            hass,
            3,
            sensor,
            True,
            {"last_reset", "max", "mean", "min", "state", "sum"},
        )
        assert stats == {sensor: expected}

    stats = get_last_short_term_statistics(
        hass,
        1,
        "sensor.test3",
        True,
        {"last_reset", "max", "mean", "min", "state", "sum"},
    )
    assert stats == {}

    instance.get_session().query(StatisticsShortTerm).delete()
    # Should not fail there is nothing in the table
    with session_scope(hass=hass, read_only=True) as session:
        stats = get_latest_short_term_statistics_with_session(
            hass,
            session,
            {"sensor.test1", "sensor.wind_direction"},
            {"last_reset", "max", "mean", "min", "state", "sum"},
        )
        assert stats == {}

    # Delete again, and manually wipe the cache since we deleted all the data
    instance.get_session().query(StatisticsShortTerm).delete()
    run_cache = get_short_term_statistics_run_cache(instance.hass)
    run_cache._latest_id_by_metadata_id = {}

    # And test again to make sure there is no data
    with session_scope(hass=hass, read_only=True) as session:
        stats = get_latest_short_term_statistics_with_session(
            hass,
            session,
            {"sensor.test1", "sensor.wind_direction"},
            {"last_reset", "max", "mean", "min", "state", "sum"},
        )
    assert stats == {}