async def test_rename_entity_collision(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    setup_recorder: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test statistics is migrated when entity_id is changed.

    This test relies on the safeguard in the statistics_meta_manager
    and should not hit the filter_unique_constraint_integrity_error safeguard.
    """
    await async_setup_component(hass, "sensor", {})

    reg_entry = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "unique_0000",
        suggested_object_id="test1",
    )
    assert reg_entry.entity_id == "sensor.test1"
    await hass.async_block_till_done()

    zero, four, states = await async_record_states(hass)
    hist = history.get_significant_states(hass, zero, four, list(states))
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)

    for kwargs in ({}, {"statistic_ids": ["sensor.test1"]}):
        stats = statistics_during_period(hass, zero, period="5minute", **kwargs)
        assert stats == {}
    stats = get_last_short_term_statistics(
        hass,
        0,
        "sensor.test1",
        True,
        {"last_reset", "max", "mean", "min", "state", "sum"},
    )
    assert stats == {}

    do_adhoc_statistics(hass, start=zero)
    await async_wait_recording_done(hass)
    expected_1 = {
        "start": process_timestamp(zero).timestamp(),
        "end": process_timestamp(zero + timedelta(minutes=5)).timestamp(),
        "mean": pytest.approx(14.915254237288135),
        "min": pytest.approx(10.0),
        "max": pytest.approx(20.0),
        "last_reset": None,
        "state": None,
        "sum": None,
    }
    expected_stats1 = [expected_1]
    expected_stats2 = [expected_1]
    expected_stats_wind_direction = [
        {
            "start": process_timestamp(zero).timestamp(),
            "end": process_timestamp(zero + timedelta(minutes=5)).timestamp(),
            "mean": pytest.approx(358.6387003873801),
            "min": None,
            "max": None,
            "last_reset": None,
            "state": None,
            "sum": None,
        }
    ]

    stats = statistics_during_period(hass, zero, period="5minute")
    assert stats == {
        "sensor.test1": expected_stats1,
        "sensor.test2": expected_stats2,
        "sensor.wind_direction": expected_stats_wind_direction,
    }

    # Insert metadata for sensor.test99
    metadata_1 = {
        "has_sum": False,
        "mean_type": StatisticMeanType.ARITHMETIC,
        "name": "Total imported energy",
        "source": "test",
        "statistic_id": "sensor.test99",
        "unit_of_measurement": "kWh",
    }

    with session_scope(hass=hass) as session:
        session.add(recorder.db_schema.StatisticsMeta.from_meta(metadata_1))

    # Rename entity sensor.test1 to sensor.test99
    entity_registry.async_update_entity("sensor.test1", new_entity_id="sensor.test99")
    await async_wait_recording_done(hass)

    # Statistics failed to migrate due to the collision
    stats = statistics_during_period(hass, zero, period="5minute")
    assert stats == {
        "sensor.test1": expected_stats1,
        "sensor.test2": expected_stats2,
        "sensor.wind_direction": expected_stats_wind_direction,
    }

    # Verify the safeguard in the states meta manager was hit
    assert (
        "Cannot rename statistic_id `sensor.test1` to `sensor.test99` "
        "because the new statistic_id is already in use"
    ) in caplog.text

    # Verify the filter_unique_constraint_integrity_error safeguard was not hit
    assert "Blocked attempt to insert duplicated statistic rows" not in caplog.text