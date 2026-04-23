async def _test_self_reset(
    hass: HomeAssistant, config, start_time, expect_reset=True
) -> None:
    """Test energy sensor self reset."""
    now = dt_util.parse_datetime(start_time)
    with freeze_time(now):
        assert await async_setup_component(hass, DOMAIN, config)
        await hass.async_block_till_done()

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        entity_id = config[DOMAIN]["energy_bill"]["source"]

        async_fire_time_changed(hass, now)
        hass.states.async_set(
            entity_id, 1, {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR}
        )
        await hass.async_block_till_done()

    now += timedelta(seconds=30)
    with freeze_time(now):
        async_fire_time_changed(hass, now)
        hass.states.async_set(
            entity_id,
            3,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    now += timedelta(seconds=30)
    with freeze_time(now):
        # Listen for events and check that state in the first event after reset is actually 0, issue #142053
        events = []

        async def handle_energy_bill_event(event):
            events.append(event)

        unsub = async_track_state_change_event(
            hass,
            "sensor.energy_bill",
            handle_energy_bill_event,
        )

        async_fire_time_changed(hass, now)
        await hass.async_block_till_done()
        unsub()
        hass.states.async_set(
            entity_id,
            6,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill")
    if expect_reset:
        assert state.attributes.get("last_period") == "2"
        assert (
            state.attributes.get("last_reset") == dt_util.as_utc(now).isoformat()
        )  # last_reset is kept in UTC
        assert state.state == "3"
        # In first event state should be 0
        assert len(events) == 2
        assert events[0].data.get("new_state").state == "0"
        assert events[1].data.get("new_state").state == "0"
    else:
        assert state.attributes.get("last_period") == "0"
        assert state.state == "5"
        start_time_str = dt_util.parse_datetime(start_time).isoformat()
        assert state.attributes.get("last_reset") == start_time_str

    # Check next day when nothing should happen for weekly, monthly, bimonthly and yearly
    if config["utility_meter"]["energy_bill"].get("cycle") in [
        QUARTER_HOURLY,
        HOURLY,
        DAILY,
    ]:
        now += timedelta(minutes=5)
    else:
        now += timedelta(days=5)
    with freeze_time(now):
        async_fire_time_changed(hass, now)
        await hass.async_block_till_done()
        hass.states.async_set(
            entity_id,
            10,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()
    state = hass.states.get("sensor.energy_bill")
    if expect_reset:
        assert state.attributes.get("last_period") == "2"
        assert state.state == "7"
    else:
        assert state.attributes.get("last_period") == "0"
        assert state.state == "9"