async def test_state_always_available(
    hass: HomeAssistant, yaml_config, config_entry_config
) -> None:
    """Test utility sensor state."""
    if yaml_config:
        assert await async_setup_component(hass, DOMAIN, yaml_config)
        await hass.async_block_till_done()
        entity_id = yaml_config[DOMAIN]["energy_bill"]["source"]
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
        entity_id = config_entry_config["source"]

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    hass.states.async_set(
        entity_id, 2, {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR}
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill")
    assert state is not None
    assert state.state == "0"
    assert state.attributes.get("status") == COLLECTING
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR

    now = dt_util.utcnow() + timedelta(seconds=10)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            3,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill")
    assert state is not None
    assert state.state == "1"
    assert state.attributes.get("status") == COLLECTING

    # test unavailable state
    hass.states.async_set(
        entity_id,
        "unavailable",
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.energy_bill")
    assert state is not None
    assert state.state == "1"

    # test unknown state
    hass.states.async_set(
        entity_id, None, {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR}
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.energy_bill")
    assert state is not None
    assert state.state == "1"