async def test_default_setup(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    dsmr_connection_fixture: tuple[MagicMock, MagicMock, MagicMock],
) -> None:
    """Test the default setup."""
    (connection_factory, _transport, _protocol) = dsmr_connection_fixture

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "2.2",
        "serial_id": "1234",
        "serial_id_gas": "5678",
    }
    entry_options = {
        "time_between_update": 0,
    }

    telegram = Telegram()
    telegram.add(
        CURRENT_ELECTRICITY_USAGE,
        CosemObject(
            (0, 0),
            [{"value": Decimal("0.0"), "unit": UnitOfPower.WATT}],
        ),
        "CURRENT_ELECTRICITY_USAGE",
    )
    telegram.add(
        ELECTRICITY_ACTIVE_TARIFF,
        CosemObject((0, 0), [{"value": "0001", "unit": ""}]),
        "ELECTRICITY_ACTIVE_TARIFF",
    )
    telegram.add(
        GAS_METER_READING,
        MBusObject(
            (0, 0),
            [
                {"value": datetime.datetime.fromtimestamp(1551642213)},
                {"value": Decimal("745.695"), "unit": UnitOfVolume.CUBIC_METERS},
            ],
        ),
        "GAS_METER_READING",
    )

    mock_entry = MockConfigEntry(
        domain="dsmr", unique_id="/dev/ttyUSB0", data=entry_data, options=entry_options
    )

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    telegram_callback = connection_factory.call_args_list[0][0][2]

    # simulate a telegram pushed from the smartmeter and parsed by dsmr_parser
    telegram_callback(telegram)

    # after receiving telegram entities need to have the chance to be created
    await hass.async_block_till_done()

    entry = entity_registry.async_get("sensor.electricity_meter_power_consumption")
    assert entry
    assert entry.unique_id == "1234_current_electricity_usage"

    entry = entity_registry.async_get("sensor.gas_meter_gas_consumption")
    assert entry
    assert entry.unique_id == "5678_gas_meter_reading"

    # make sure entities are initialized
    power_consumption = hass.states.get("sensor.electricity_meter_power_consumption")
    assert power_consumption.state == "0.0"
    assert (
        power_consumption.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.POWER
    )
    assert (
        power_consumption.attributes.get(ATTR_STATE_CLASS)
        == SensorStateClass.MEASUREMENT
    )
    assert power_consumption.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "W"

    telegram = Telegram()
    telegram.add(
        CURRENT_ELECTRICITY_USAGE,
        CosemObject(
            (0, 0),
            [{"value": Decimal("35.0"), "unit": UnitOfPower.WATT}],
        ),
        "CURRENT_ELECTRICITY_USAGE",
    )
    telegram.add(
        ELECTRICITY_ACTIVE_TARIFF,
        CosemObject((0, 0), [{"value": "0001", "unit": ""}]),
        "ELECTRICITY_ACTIVE_TARIFF",
    )
    telegram.add(
        GAS_METER_READING,
        MBusObject(
            (0, 0),
            [
                {"value": datetime.datetime.fromtimestamp(1551642214)},
                {"value": Decimal("745.701"), "unit": UnitOfVolume.CUBIC_METERS},
            ],
        ),
        "GAS_METER_READING",
    )

    # simulate a telegram pushed from the smartmeter and parsed by dsmr_parser
    telegram_callback(telegram)

    # after receiving telegram entities need to have the chance to be created
    await hass.async_block_till_done()

    # ensure entities have new state value after incoming telegram
    power_consumption = hass.states.get("sensor.electricity_meter_power_consumption")
    assert power_consumption.state == "35.0"
    assert power_consumption.attributes.get("unit_of_measurement") == UnitOfPower.WATT

    # tariff should be translated in human readable and have no unit
    active_tariff = hass.states.get("sensor.electricity_meter_active_tariff")
    assert active_tariff.state == "low"
    assert active_tariff.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENUM
    assert (
        active_tariff.attributes.get(ATTR_FRIENDLY_NAME)
        == "Electricity Meter Active tariff"
    )
    assert active_tariff.attributes.get(ATTR_OPTIONS) == ["low", "normal"]
    assert active_tariff.attributes.get(ATTR_STATE_CLASS) is None
    assert active_tariff.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None

    # check if gas consumption is parsed correctly
    gas_consumption = hass.states.get("sensor.gas_meter_gas_consumption")
    assert gas_consumption.state == "745.701"
    assert gas_consumption.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.GAS
    assert (
        gas_consumption.attributes.get(ATTR_FRIENDLY_NAME)
        == "Gas Meter Gas consumption"
    )
    assert (
        gas_consumption.attributes.get(ATTR_STATE_CLASS)
        == SensorStateClass.TOTAL_INCREASING
    )
    assert (
        gas_consumption.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfVolume.CUBIC_METERS
    )