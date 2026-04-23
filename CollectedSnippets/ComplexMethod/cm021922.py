async def test_non_periodically_resetting(
    hass: HomeAssistant, yaml_config, config_entry_config
) -> None:
    """Test utility meter "non periodically resetting" mode."""
    # Home assistant is not runnit yet
    hass.set_state(CoreState.not_running)

    now = dt_util.utcnow()
    with freeze_time(now):
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
                version=2,
            )
            config_entry.add_to_hass(hass)
            assert await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()
            entity_id = config_entry_config["source"]

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)

        async_fire_time_changed(hass, now)
        hass.states.async_set(
            entity_id, 1, {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR}
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill")
    assert state.attributes.get("status") == COLLECTING

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

    state = hass.states.get("sensor.energy_bill")
    assert state.state == "2"
    assert state.attributes.get("last_valid_state") == "3"
    assert state.attributes.get("status") == COLLECTING

    now += timedelta(seconds=30)
    with freeze_time(now):
        async_fire_time_changed(hass, now)
        hass.states.async_set(
            entity_id,
            STATE_UNKNOWN,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill")
    assert state.state == "2"
    assert state.attributes.get("last_valid_state") == "3"
    assert state.attributes.get("status") == COLLECTING

    now += timedelta(seconds=30)
    with freeze_time(now):
        async_fire_time_changed(hass, now)
        hass.states.async_set(
            entity_id,
            6,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill")
    assert state.state == "5"
    assert state.attributes.get("last_valid_state") == "6"
    assert state.attributes.get("status") == COLLECTING

    now += timedelta(seconds=30)
    with freeze_time(now):
        async_fire_time_changed(hass, now)
        await hass.async_block_till_done()
        hass.states.async_set(
            entity_id,
            9,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill")
    assert state.state == "8"
    assert state.attributes.get("last_valid_state") == "9"
    assert state.attributes.get("status") == COLLECTING