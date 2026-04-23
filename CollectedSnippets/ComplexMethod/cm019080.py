async def test_no_change(
    hass: HomeAssistant,
    extra_config: dict[str, Any],
    force_update: bool,
    attributes: list[dict[str, Any]],
) -> None:
    """Test derivative sensor state updated when source sensor doesn't change."""
    events: list[Event[EventStateChangedData]] = []

    @callback
    def _capture_event(event: Event) -> None:
        events.append(event)

    async_track_state_change_event(hass, "sensor.derivative", _capture_event)

    config = {
        "sensor": {
            "platform": "derivative",
            "name": "derivative",
            "source": "sensor.energy",
            "unit": "kW",
            "round": 2,
        }
        | extra_config
    }

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    entity_id = config["sensor"]["source"]
    base = dt_util.utcnow()
    with freeze_time(base) as freezer:
        for value, extra_attributes in zip([0, 1, 1, 1], attributes, strict=True):
            hass.states.async_set(
                entity_id, value, extra_attributes, force_update=force_update
            )
            await hass.async_block_till_done()

            freezer.move_to(dt_util.utcnow() + timedelta(seconds=3600))

    state = hass.states.get("sensor.derivative")
    assert state is not None

    await hass.async_block_till_done()
    await hass.async_block_till_done()
    states = [events[0].data["new_state"].state] + [
        round(float(event.data["new_state"].state), config["sensor"]["round"])
        for event in events[1:]
    ]
    # Testing a energy sensor at 1 kWh for 1hour = 0kW
    assert states == ["unavailable", 0.0, 1.0, 0.0]

    state = events[-1].data["new_state"]

    assert state.attributes.get("unit_of_measurement") == "kW"

    assert state.last_changed == base + timedelta(seconds=2 * 3600)