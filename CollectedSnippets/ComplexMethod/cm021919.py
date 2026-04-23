async def test_service_reset_no_tariffs(
    hass: HomeAssistant, yaml_config, config_entry_config
) -> None:
    """Test utility sensor service reset for sensor with no tariffs."""
    # Home assistant is not runnit yet
    hass.state = CoreState.not_running
    last_reset = "2023-10-01T00:00:00+00:00"

    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(
                    "sensor.energy_bill",
                    "3",
                    attributes={
                        ATTR_LAST_RESET: last_reset,
                    },
                ),
                {
                    "native_value": {
                        "__type": "<class 'decimal.Decimal'>",
                        "decimal_str": "3",
                    },
                    "native_unit_of_measurement": "kWh",
                    "last_reset": last_reset,
                    "last_period": "0",
                    "last_valid_state": None,
                    "status": "collecting",
                    "input_device_class": "energy",
                },
            ),
        ],
    )

    if yaml_config:
        assert await async_setup_component(hass, DOMAIN, yaml_config)
        await hass.async_block_till_done()
    else:
        config_entry = MockConfigEntry(
            data={},
            domain=DOMAIN,
            options=config_entry_config,
            title=config_entry_config["name"],
        )
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill")
    assert state
    assert state.state == "3"
    assert state.attributes.get("last_reset") == last_reset
    assert state.attributes.get("last_period") == "0"

    now = dt_util.utcnow()
    with freeze_time(now):
        await hass.services.async_call(
            domain=DOMAIN,
            service=SERVICE_RESET,
            service_data={},
            target={"entity_id": "sensor.energy_bill"},
            blocking=True,
        )

        await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill")
    assert state
    assert state.state == "0"
    assert state.attributes.get("last_reset") == now.isoformat()
    assert state.attributes.get("last_period") == "3"