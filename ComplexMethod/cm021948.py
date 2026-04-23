async def test_v5_meter(
    hass: HomeAssistant,
    dsmr_connection_fixture: tuple[MagicMock, MagicMock, MagicMock],
    value: Decimal,
    state: str,
) -> None:
    """Test if v5 meter is correctly parsed."""
    (connection_factory, _transport, _protocol) = dsmr_connection_fixture

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "5",
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
                {"value": value, "unit": "m3"},
            ],
        ),
        "HOURLY_GAS_METER_READING",
    )
    telegram.add(
        ELECTRICITY_ACTIVE_TARIFF,
        CosemObject((0, 0), [{"value": "0001", "unit": ""}]),
        "ELECTRICITY_ACTIVE_TARIFF",
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

    # tariff should be translated in human readable and have no unit
    active_tariff = hass.states.get("sensor.electricity_meter_active_tariff")
    assert active_tariff.state == "low"
    assert active_tariff.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENUM
    assert active_tariff.attributes.get(ATTR_OPTIONS) == ["low", "normal"]
    assert active_tariff.attributes.get(ATTR_STATE_CLASS) is None
    assert active_tariff.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None

    # check if gas consumption is parsed correctly
    gas_consumption = hass.states.get("sensor.gas_meter_gas_consumption")
    assert gas_consumption.state == state
    assert gas_consumption.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.GAS
    assert (
        gas_consumption.attributes.get(ATTR_STATE_CLASS)
        == SensorStateClass.TOTAL_INCREASING
    )
    assert (
        gas_consumption.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfVolume.CUBIC_METERS
    )