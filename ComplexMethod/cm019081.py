async def test_data_moving_average_with_zeroes(
    hass: HomeAssistant,
    extra_config: dict[str, Any],
    force_update: bool,
    attributes: list[dict[str, Any]],
) -> None:
    """Test that zeroes are properly handled within the time window."""
    # We simulate the following situation:
    # The temperature rises 1 °C per minute for 10 minutes long. Then, it
    # stays constant for another 10 minutes. There is a data point every
    # minute and we use a time window of 10 minutes.
    # Therefore, we can expect the derivative to peak at 1 after 10 minutes
    # and then fall down to 0 in steps of 10%.

    events: list[Event[EventStateChangedData]] = []

    @callback
    def _capture_event(event: Event) -> None:
        events.append(event)

    async_track_state_change_event(hass, "sensor.power", _capture_event)

    temperature_values = []
    for temperature in range(10):
        temperature_values += [temperature]
    temperature_values += [10] * 11
    time_window = 600
    times = list(range(0, 1200 + 60, 60))

    config, entity_id = await _setup_sensor(
        hass,
        {
            "time_window": {"seconds": time_window},
            "unit_time": UnitOfTime.MINUTES,
            "round": 1,
        }
        | extra_config,
    )

    base = dt_util.utcnow()
    with freeze_time(base) as freezer:
        last_derivative = 0
        for time, value, extra_attributes in zip(
            times, temperature_values, attributes, strict=True
        ):
            now = base + timedelta(seconds=time)
            freezer.move_to(now)
            hass.states.async_set(
                entity_id, value, extra_attributes, force_update=force_update
            )

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert len(events[1:]) == len(times)
    for time, event in zip(times, events[1:], strict=True):
        state = event.data["new_state"]
        derivative = round(float(state.state), config["sensor"]["round"])

        if time_window == time:
            assert derivative == 1.0
        elif time_window < time < time_window * 2:
            assert (0.1 - 1e-6) < abs(derivative - last_derivative) < (0.1 + 1e-6)
        elif time == time_window * 2:
            assert derivative == 0

        last_derivative = derivative