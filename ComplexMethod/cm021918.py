async def test_restore_state(
    hass: HomeAssistant, yaml_config, config_entry_config
) -> None:
    """Test utility sensor restore state."""
    # Home assistant is not runnit yet
    hass.set_state(CoreState.not_running)

    last_reset_1 = "2020-12-21T00:00:00.013073+00:00"
    last_reset_2 = "2020-12-22T00:00:00.013073+00:00"

    mock_restore_cache_with_extra_data(
        hass,
        [
            # sensor.energy_bill_tariff0 is restored as expected, including device
            # class
            (
                State(
                    "sensor.energy_bill_tariff0",
                    "0.1",
                    attributes={
                        ATTR_STATUS: PAUSED,
                        ATTR_LAST_RESET: last_reset_1,
                        ATTR_UNIT_OF_MEASUREMENT: UnitOfVolume.CUBIC_METERS,
                    },
                ),
                {
                    "native_value": {
                        "__type": "<class 'decimal.Decimal'>",
                        "decimal_str": "0.2",
                    },
                    "native_unit_of_measurement": "gal",
                    "last_reset": last_reset_2,
                    "last_period": "1.3",
                    "last_valid_state": None,
                    "status": "collecting",
                    "input_device_class": "water",
                },
            ),
            # sensor.energy_bill_tariff1 is restored as expected, except device
            # class
            (
                State(
                    "sensor.energy_bill_tariff1",
                    "1.1",
                    attributes={
                        ATTR_STATUS: PAUSED,
                        ATTR_LAST_RESET: last_reset_1,
                        ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.MEGA_WATT_HOUR,
                    },
                ),
                {
                    "native_value": {
                        "__type": "<class 'decimal.Decimal'>",
                        "decimal_str": "1.2",
                    },
                    "native_unit_of_measurement": "kWh",
                    "last_reset": last_reset_2,
                    "last_period": "1.3",
                    "last_valid_state": None,
                    "status": "paused",
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

    # restore from cache
    state = hass.states.get("sensor.energy_bill_tariff0")
    assert state.state == "0.2"
    assert state.attributes.get("status") == COLLECTING
    assert state.attributes.get("last_reset") == last_reset_2
    assert state.attributes.get("last_valid_state") == "None"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfVolume.GALLONS
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.WATER

    state = hass.states.get("sensor.energy_bill_tariff1")
    assert state.state == "1.2"
    assert state.attributes.get("status") == PAUSED
    assert state.attributes.get("last_reset") == last_reset_2
    assert state.attributes.get("last_valid_state") == "None"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY

    # utility_meter is loaded, now set sensors according to utility_meter:

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    state = hass.states.get("select.energy_bill")
    assert state.state == "tariff0"

    state = hass.states.get("sensor.energy_bill_tariff0")
    assert state.attributes.get("status") == COLLECTING

    for entity_id in ("sensor.energy_bill_tariff1",):
        state = hass.states.get(entity_id)
        assert state.attributes.get("status") == PAUSED