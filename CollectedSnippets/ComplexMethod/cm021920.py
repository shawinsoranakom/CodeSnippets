async def test_service_reset_no_tariffs_correct_with_multi(
    hass: HomeAssistant, yaml_config, config_entry_configs
) -> None:
    """Test complex utility sensor service reset for multiple sensors with no tarrifs.

    See GitHub issue #114864: Service "utility_meter.reset" affects all meters.
    """

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
                ),
                {
                    "native_value": {
                        "__type": "<class 'decimal.Decimal'>",
                        "decimal_str": "3",
                    },
                    "native_unit_of_measurement": "kWh",
                    "last_reset": last_reset,
                    "last_period": "0",
                    "status": "collecting",
                },
            ),
            (
                State(
                    "sensor.water_bill",
                    "6",
                ),
                {
                    "native_value": {
                        "__type": "<class 'decimal.Decimal'>",
                        "decimal_str": "6",
                    },
                    "native_unit_of_measurement": "kWh",
                    "last_reset": last_reset,
                    "last_period": "0",
                    "status": "collecting",
                },
            ),
        ],
    )

    if yaml_config:
        assert await async_setup_component(hass, DOMAIN, yaml_config)
        await hass.async_block_till_done()
    else:
        for entry in config_entry_configs:
            config_entry = MockConfigEntry(
                data={},
                domain=DOMAIN,
                options=entry,
                title=entry["name"],
            )
            config_entry.add_to_hass(hass)
            assert await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill")
    assert state
    assert state.state == "3"
    assert state.attributes.get("last_reset") == last_reset
    assert state.attributes.get("last_period") == "0"

    state = hass.states.get("sensor.water_bill")
    assert state
    assert state.state == "6"
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

    state = hass.states.get("sensor.water_bill")
    assert state
    assert state.state == "6"
    assert state.attributes.get("last_reset") == last_reset
    assert state.attributes.get("last_period") == "0"