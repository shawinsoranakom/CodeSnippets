async def test_left(
    hass: HomeAssistant,
    sequence: tuple[tuple[float, float, dict[str, Any], float], ...],
    force_update: bool,
    extra_config: dict[str, Any],
    expected_states: tuple[float, ...],
) -> None:
    """Test integration sensor state with left Riemann method."""
    events: list[Event[EventStateChangedData]] = []

    @callback
    def _capture_event(event: Event) -> None:
        events.append(event)

    async_track_state_change_event(hass, "sensor.integration", _capture_event)

    config = {
        "sensor": {
            "platform": "integration",
            "name": "integration",
            "method": "left",
            "source": "sensor.power",
            "round": 2,
        }
        | extra_config
    }

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.integration")
    assert state.state == STATE_UNKNOWN

    entity_id = config["sensor"]["source"]
    hass.states.async_set(
        entity_id, 0, {ATTR_UNIT_OF_MEASUREMENT: UnitOfPower.KILO_WATT}
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.integration")
    assert state.state == STATE_UNKNOWN

    # Testing a power sensor with non-monotonic intervals and values
    start_time = dt_util.utcnow()
    with freeze_time(start_time) as freezer:
        for time, value, extra_attributes in sequence:
            freezer.move_to(start_time + timedelta(minutes=time))
            hass.states.async_set(
                entity_id,
                value,
                {ATTR_UNIT_OF_MEASUREMENT: UnitOfPower.KILO_WATT} | extra_attributes,
                force_update=force_update,
            )

    await hass.async_block_till_done()
    await hass.async_block_till_done()
    states = (
        [events[0].data["new_state"].state]
        + [events[1].data["new_state"].state]
        + [
            round(float(event.data["new_state"].state), config["sensor"]["round"])
            for event in events[2:]
        ]
    )
    assert states == ["unknown", "unknown", *expected_states]

    state = events[-1].data["new_state"]
    assert state.attributes.get("unit_of_measurement") == UnitOfEnergy.KILO_WATT_HOUR