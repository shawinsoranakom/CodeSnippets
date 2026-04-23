async def test_compile_hourly_sum_statistics_negative_state(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    entity_id,
    warning_1,
    warning_2,
    state_class,
    device_class,
    state_unit,
    display_unit,
    statistics_unit,
    unit_class,
    offset,
) -> None:
    """Test compiling hourly statistics with negative states."""
    zero = get_start_time(dt_util.utcnow())
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS)

    mocksensor = MockSensor(name="custom_sensor")
    mocksensor._attr_should_poll = False
    setup_test_component_platform(hass, DOMAIN, [mocksensor], built_in=False)

    await async_setup_component(hass, "homeassistant", {})
    with freeze_time(zero) as freezer:
        await async_setup_component(
            hass, "sensor", {"sensor": [{"platform": "demo"}, {"platform": "test"}]}
        )
        await hass.async_block_till_done()
    attributes = {
        "device_class": device_class,
        "state_class": state_class,
        "unit_of_measurement": state_unit,
    }
    seq = [15, 16, 15, 16, 20, -20, 20, 10]

    states = {entity_id: []}
    offending_state = 5
    if state := hass.states.get(entity_id):
        states[entity_id].append(state)
        offending_state = 6
    one = zero
    with freeze_time(zero) as freezer:
        for i in range(len(seq)):
            one = one + timedelta(seconds=5)
            _states = await async_record_meter_state(
                hass, freezer, one, entity_id, attributes, seq[i : i + 1]
            )
            states[entity_id].extend(_states[entity_id])
    await async_wait_recording_done(hass)

    hist = history.get_significant_states(
        hass,
        zero - timedelta.resolution,
        one + timedelta.resolution,
        hass.states.async_entity_ids(),
        significant_changes_only=False,
    )
    assert_multiple_states_equal_without_context_and_last_changed(
        dict(states)[entity_id], dict(hist)[entity_id]
    )

    do_adhoc_statistics(hass, start=zero)
    await async_wait_recording_done(hass)
    statistic_ids = await async_list_statistic_ids(hass)
    assert {
        "display_unit_of_measurement": display_unit,
        "has_mean": False,
        "mean_type": StatisticMeanType.NONE,
        "has_sum": True,
        "name": None,
        "source": "recorder",
        "statistic_id": entity_id,
        "statistics_unit_of_measurement": statistics_unit,
        "unit_class": unit_class,
    } in statistic_ids
    stats = statistics_during_period(hass, zero, period="5minute")
    assert stats[entity_id] == [
        {
            "start": process_timestamp(zero).timestamp(),
            "end": process_timestamp(zero + timedelta(minutes=5)).timestamp(),
            "max": None,
            "mean": None,
            "min": None,
            "last_reset": None,
            "state": pytest.approx(seq[7]),
            "sum": pytest.approx(offset + 15),  # (20 - 15) + (10 - 0)
        },
    ]
    assert "Error while processing event StatisticsTask" not in caplog.text
    state = states[entity_id][offending_state].state
    last_updated = states[entity_id][offending_state].last_updated.isoformat()
    assert (
        f"Entity {entity_id} {warning_1}has state class total_increasing, but its state "
        f"is negative. Triggered by state {state} with last_updated set to {last_updated}."
        in caplog.text
    )
    assert warning_2 in caplog.text