async def test_sensors(hass: HomeAssistant, device_registry: dr.DeviceRegistry) -> None:
    """Test creation of the sensors."""

    mock_powerwall = await _mock_powerwall_with_fixtures(hass)

    config_entry = MockConfigEntry(domain=DOMAIN, data={CONF_IP_ADDRESS: "1.2.3.4"})
    config_entry.add_to_hass(hass)
    with (
        patch(
            "homeassistant.components.powerwall.config_flow.Powerwall",
            return_value=mock_powerwall,
        ),
        patch(
            "homeassistant.components.powerwall.Powerwall", return_value=mock_powerwall
        ),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    reg_device = device_registry.async_get_device(
        identifiers={("powerwall", MOCK_GATEWAY_DIN)},
    )
    assert reg_device.model == "PowerWall 2 (GW1)"
    assert reg_device.sw_version == "1.50.1 c58c2df3"
    assert reg_device.manufacturer == "Tesla"
    assert reg_device.name == "MySite"

    state = hass.states.get("sensor.mysite_load_power")
    assert state.state == "1.971"
    attributes = state.attributes
    assert attributes[ATTR_DEVICE_CLASS] == "power"
    assert attributes[ATTR_UNIT_OF_MEASUREMENT] == "kW"
    assert attributes[ATTR_STATE_CLASS] == "measurement"
    assert attributes[ATTR_FRIENDLY_NAME] == "MySite Load power"

    state = hass.states.get("sensor.mysite_load_frequency")
    assert state.state == "60"
    attributes = state.attributes
    assert attributes[ATTR_DEVICE_CLASS] == "frequency"
    assert attributes[ATTR_UNIT_OF_MEASUREMENT] == "Hz"
    assert attributes[ATTR_STATE_CLASS] == "measurement"
    assert attributes[ATTR_FRIENDLY_NAME] == "MySite Load frequency"

    state = hass.states.get("sensor.mysite_load_voltage")
    assert state.state == "120.7"
    attributes = state.attributes
    assert attributes[ATTR_DEVICE_CLASS] == "voltage"
    assert attributes[ATTR_UNIT_OF_MEASUREMENT] == "V"
    assert attributes[ATTR_STATE_CLASS] == "measurement"
    assert attributes[ATTR_FRIENDLY_NAME] == "MySite Load voltage"

    state = hass.states.get("sensor.mysite_load_current")
    assert state.state == "0"
    attributes = state.attributes
    assert attributes[ATTR_DEVICE_CLASS] == "current"
    assert attributes[ATTR_UNIT_OF_MEASUREMENT] == "A"
    assert attributes[ATTR_STATE_CLASS] == "measurement"
    assert attributes[ATTR_FRIENDLY_NAME] == "MySite Load current"

    assert float(hass.states.get("sensor.mysite_load_export").state) == 1056.8
    assert float(hass.states.get("sensor.mysite_load_import").state) == 4693.0

    state = hass.states.get("sensor.mysite_battery_power")
    assert state.state == "-8.55"

    assert float(hass.states.get("sensor.mysite_battery_export").state) == 3620.0
    assert float(hass.states.get("sensor.mysite_battery_import").state) == 4216.2

    state = hass.states.get("sensor.mysite_solar_power")
    assert state.state == "10.49"

    assert float(hass.states.get("sensor.mysite_solar_export").state) == 9864.2
    assert float(hass.states.get("sensor.mysite_solar_import").state) == 28.2

    state = hass.states.get("sensor.mysite_charge")
    assert state.state == "47"
    expected_attributes = {
        "unit_of_measurement": PERCENTAGE,
        "friendly_name": "MySite Charge",
        "device_class": "battery",
    }
    # Only test for a subset of attributes in case
    # HA changes the implementation and a new one appears
    for key, value in expected_attributes.items():
        assert state.attributes[key] == value

    state = hass.states.get("sensor.mysite_backup_reserve")
    assert state.state == "15"
    expected_attributes = {
        "unit_of_measurement": PERCENTAGE,
        "friendly_name": "MySite Backup reserve",
    }
    # Only test for a subset of attributes in case
    # HA changes the implementation and a new one appears
    for key, value in expected_attributes.items():
        assert state.attributes[key] == value

    mock_powerwall.get_meters.return_value = MetersAggregatesResponse.from_dict({})
    mock_powerwall.get_backup_reserve_percentage.return_value = None

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=60))
    await hass.async_block_till_done()

    assert hass.states.get("sensor.mysite_load_power").state == STATE_UNKNOWN
    assert hass.states.get("sensor.mysite_load_frequency").state == STATE_UNKNOWN
    assert hass.states.get("sensor.mysite_backup_reserve").state == STATE_UNKNOWN

    assert (
        float(hass.states.get("sensor.mysite_tg0123456789ab_battery_capacity").state)
        == 14.715
    )
    assert (
        float(hass.states.get("sensor.mysite_tg0123456789ab_battery_voltage").state)
        == 245.7
    )
    assert (
        float(hass.states.get("sensor.mysite_tg0123456789ab_frequency").state) == 50.0
    )
    assert float(hass.states.get("sensor.mysite_tg0123456789ab_current").state) == 0.3
    assert int(hass.states.get("sensor.mysite_tg0123456789ab_power").state) == -100
    assert (
        float(hass.states.get("sensor.mysite_tg0123456789ab_battery_export").state)
        == 2358.235
    )
    assert (
        float(hass.states.get("sensor.mysite_tg0123456789ab_battery_import").state)
        == 2693.355
    )
    assert (
        float(hass.states.get("sensor.mysite_tg0123456789ab_battery_remaining").state)
        == 14.715
    )
    assert (
        str(hass.states.get("sensor.mysite_tg0123456789ab_grid_state").state)
        == "grid_compliant"
    )
    assert (
        float(hass.states.get("sensor.mysite_tg9876543210ba_battery_capacity").state)
        == 15.137
    )
    assert (
        float(hass.states.get("sensor.mysite_tg9876543210ba_battery_voltage").state)
        == 245.6
    )
    assert (
        float(hass.states.get("sensor.mysite_tg9876543210ba_frequency").state) == 50.0
    )
    assert float(hass.states.get("sensor.mysite_tg9876543210ba_current").state) == 0.1
    assert int(hass.states.get("sensor.mysite_tg9876543210ba_power").state) == -100
    assert (
        float(hass.states.get("sensor.mysite_tg9876543210ba_battery_export").state)
        == 509.907
    )
    assert (
        float(hass.states.get("sensor.mysite_tg9876543210ba_battery_import").state)
        == 610.483
    )
    assert (
        float(hass.states.get("sensor.mysite_tg9876543210ba_battery_remaining").state)
        == 15.137
    )
    assert (
        str(hass.states.get("sensor.mysite_tg9876543210ba_grid_state").state)
        == "grid_compliant"
    )