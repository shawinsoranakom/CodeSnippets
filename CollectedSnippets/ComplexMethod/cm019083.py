async def test_unavailable_boot(
    restore_state,
    hass: HomeAssistant,
) -> None:
    """Test that the booting sequence does not leave derivative in a bad state."""

    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(
                    "sensor.power",
                    restore_state,
                    {"unit_of_measurement": "kW", "device_class": "power"},
                ),
                {
                    "native_value": restore_state,
                    "native_unit_of_measurement": "kW",
                },
            ),
        ],
    )

    config = {
        "platform": "derivative",
        "name": "power",
        "source": "sensor.energy",
        "round": 2,
        "unit_time": "h",
    }

    config = {"sensor": config}
    entity_id = config["sensor"]["source"]
    hass.states.async_set(
        entity_id,
        STATE_UNAVAILABLE,
        {"unit_of_measurement": "kWh", "device_class": "energy"},
    )
    await hass.async_block_till_done()

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.power")
    assert state is not None
    # Sensor is unavailable as source is unavailable
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes.get(ATTR_DEVICE_CLASS) == "power"

    base = dt_util.utcnow()
    with freeze_time(base) as freezer:
        freezer.move_to(base + timedelta(hours=1))
        hass.states.async_set(
            entity_id, 10, {"unit_of_measurement": "kWh", "device_class": "energy"}
        )
        await hass.async_block_till_done()

        state = hass.states.get("sensor.power")
        assert state is not None
        # The source sensor has moved to a valid value, but we need 2 points to derive,
        # so just hold until the next tick
        assert state.state == restore_state

        freezer.move_to(base + timedelta(hours=2))
        hass.states.async_set(
            entity_id, 15, {"unit_of_measurement": "kWh", "device_class": "energy"}
        )
        await hass.async_block_till_done()

        state = hass.states.get("sensor.power")
        assert state is not None
        # Now that the source sensor has two valid datapoints, we can calculate derivative
        assert state.state == "5.00"
        assert state.attributes.get("unit_of_measurement") == "kW"