async def test_luxembourg_meter(
    hass: HomeAssistant, dsmr_connection_fixture: tuple[MagicMock, MagicMock, MagicMock]
) -> None:
    """Test if v5 meter is correctly parsed."""
    (connection_factory, _transport, _protocol) = dsmr_connection_fixture

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "5L",
        "serial_id": "1234",
        "serial_id_gas": "5678",
    }
    entry_options = {
        "time_between_update": 0,
    }

    telegram = Telegram()
    telegram.add(
        HOURLY_GAS_METER_READING,
        MBusObject(
            (0, 0),
            [
                {"value": datetime.datetime.fromtimestamp(1551642213)},
                {"value": Decimal("745.695"), "unit": "m3"},
            ],
        ),
        "HOURLY_GAS_METER_READING",
    )
    telegram.add(
        ELECTRICITY_IMPORTED_TOTAL,
        CosemObject(
            (0, 0),
            [{"value": Decimal("123.456"), "unit": UnitOfEnergy.KILO_WATT_HOUR}],
        ),
        "ELECTRICITY_IMPORTED_TOTAL",
    )
    telegram.add(
        ELECTRICITY_EXPORTED_TOTAL,
        CosemObject(
            (0, 0),
            [{"value": Decimal("654.321"), "unit": UnitOfEnergy.KILO_WATT_HOUR}],
        ),
        "ELECTRICITY_EXPORTED_TOTAL",
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

    active_tariff = hass.states.get("sensor.electricity_meter_energy_consumption_total")
    assert active_tariff.state == "123.456"
    assert active_tariff.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY
    assert (
        active_tariff.attributes.get(ATTR_STATE_CLASS)
        == SensorStateClass.TOTAL_INCREASING
    )
    assert (
        active_tariff.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfEnergy.KILO_WATT_HOUR
    )

    active_tariff = hass.states.get("sensor.electricity_meter_energy_production_total")
    assert active_tariff.state == "654.321"
    assert (
        active_tariff.attributes.get("unit_of_measurement")
        == UnitOfEnergy.KILO_WATT_HOUR
    )

    # check if gas consumption is parsed correctly
    gas_consumption = hass.states.get("sensor.gas_meter_gas_consumption")
    assert gas_consumption.state == "745.695"
    assert gas_consumption.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.GAS
    assert (
        gas_consumption.attributes.get(ATTR_STATE_CLASS)
        == SensorStateClass.TOTAL_INCREASING
    )
    assert (
        gas_consumption.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfVolume.CUBIC_METERS
    )