async def test_device_class(
    hass: HomeAssistant,
    yaml_config,
    config_entry_configs,
    energy_sensor_attributes,
    gas_sensor_attributes,
    energy_meter_attributes,
    gas_meter_attributes,
) -> None:
    """Test utility device_class."""
    if yaml_config:
        assert await async_setup_component(hass, DOMAIN, yaml_config)
        await hass.async_block_till_done()
    else:
        for config_entry_config in config_entry_configs:
            config_entry = MockConfigEntry(
                data={},
                domain=DOMAIN,
                options=config_entry_config,
                title=config_entry_config["name"],
            )
            config_entry.add_to_hass(hass)
            assert await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()

    entity_id_energy = "sensor.energy"
    entity_id_gas = "sensor.gas"

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)

    await hass.async_block_till_done()

    hass.states.async_set(entity_id_energy, 2, energy_sensor_attributes)
    hass.states.async_set(entity_id_gas, 2, gas_sensor_attributes)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_meter")
    assert state is not None
    assert state.state == "0"
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.TOTAL
    for attr, value in energy_meter_attributes.items():
        assert state.attributes.get(attr) == value

    state = hass.states.get("sensor.gas_meter")
    assert state is not None
    assert state.state == "0"
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.TOTAL_INCREASING
    for attr, value in gas_meter_attributes.items():
        assert state.attributes.get(attr) == value