async def test_services_config_entry(hass: HomeAssistant) -> None:
    """Test energy sensor reset service."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "Energy bill",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": "sensor.energy",
            "tariffs": ["peak", "offpeak"],
        },
        title="Energy bill",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "Energy bill2",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": "sensor.energy",
            "tariffs": ["peak", "offpeak"],
        },
        title="Energy bill2",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    entity_id = "sensor.energy"
    hass.states.async_set(
        entity_id, 1, {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR}
    )
    await hass.async_block_till_done()

    now = dt_util.utcnow() + timedelta(seconds=10)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            3,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill_peak")
    assert state.state == "2"

    state = hass.states.get("sensor.energy_bill_offpeak")
    assert state.state == "0"

    # Change tariff
    data = {ATTR_ENTITY_ID: "select.energy_bill", "option": "offpeak"}
    await hass.services.async_call(SELECT_DOMAIN, SERVICE_SELECT_OPTION, data)
    await hass.async_block_till_done()

    now += timedelta(seconds=10)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            4,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill_peak")
    assert state.state == "2"

    state = hass.states.get("sensor.energy_bill_offpeak")
    assert state.state == "1"

    # Change tariff
    data = {ATTR_ENTITY_ID: "select.energy_bill", "option": "wrong_tariff"}
    await hass.services.async_call(SELECT_DOMAIN, SERVICE_SELECT_OPTION, data)
    await hass.async_block_till_done()

    # Inexisting tariff, ignoring
    assert hass.states.get("select.energy_bill").state != "wrong_tariff"

    data = {ATTR_ENTITY_ID: "select.energy_bill", "option": "peak"}
    await hass.services.async_call(SELECT_DOMAIN, SERVICE_SELECT_OPTION, data)
    await hass.async_block_till_done()

    now += timedelta(seconds=10)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            5,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill_peak")
    assert state.state == "3"

    state = hass.states.get("sensor.energy_bill_offpeak")
    assert state.state == "1"

    # Reset meters
    data = {ATTR_ENTITY_ID: "select.energy_bill"}
    await hass.services.async_call(DOMAIN, SERVICE_RESET, data)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_bill_peak")
    assert state.state == "0"

    state = hass.states.get("sensor.energy_bill_offpeak")
    assert state.state == "0"

    # meanwhile energy_bill2_peak accumulated all kWh
    state = hass.states.get("sensor.energy_bill2_peak")
    assert state.state == "4"