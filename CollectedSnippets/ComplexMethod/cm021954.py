async def test_easymeter(
    hass: HomeAssistant, dsmr_connection_fixture: tuple[MagicMock, MagicMock, MagicMock]
) -> None:
    """Test if Q3D meter is correctly parsed."""
    (connection_factory, _transport, _protocol) = dsmr_connection_fixture

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "Q3D",
        "serial_id": None,
        "serial_id_gas": None,
    }
    entry_options = {
        "time_between_update": 0,
    }

    telegram = Telegram()
    telegram.add(
        ELECTRICITY_IMPORTED_TOTAL,
        CosemObject(
            (0, 0),
            [{"value": Decimal("54184.6316"), "unit": UnitOfEnergy.KILO_WATT_HOUR}],
        ),
        "ELECTRICITY_IMPORTED_TOTAL",
    )
    telegram.add(
        ELECTRICITY_EXPORTED_TOTAL,
        CosemObject(
            (0, 0),
            [{"value": Decimal("19981.1069"), "unit": UnitOfEnergy.KILO_WATT_HOUR}],
        ),
        "ELECTRICITY_EXPORTED_TOTAL",
    )

    mock_entry = MockConfigEntry(
        domain="dsmr",
        unique_id="/dev/ttyUSB0",
        data=entry_data,
        options=entry_options,
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
    assert active_tariff.state == "54184.632"
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
    assert active_tariff.state == "19981.107"
    assert (
        active_tariff.attributes.get(ATTR_STATE_CLASS)
        == SensorStateClass.TOTAL_INCREASING
    )
    assert (
        active_tariff.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfEnergy.KILO_WATT_HOUR
    )