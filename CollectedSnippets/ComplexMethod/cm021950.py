async def test_belgian_meter(
    hass: HomeAssistant, dsmr_connection_fixture: tuple[MagicMock, MagicMock, MagicMock]
) -> None:
    """Test if Belgian meter is correctly parsed."""
    (connection_factory, _transport, _protocol) = dsmr_connection_fixture

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "5B",
        "serial_id": "1234",
        "serial_id_gas": None,
    }
    entry_options = {
        "time_between_update": 0,
    }

    telegram = Telegram()
    telegram.add(
        BELGIUM_CURRENT_AVERAGE_DEMAND,
        CosemObject(
            (0, 0),
            [{"value": Decimal("1.75"), "unit": "kW"}],
        ),
        "BELGIUM_CURRENT_AVERAGE_DEMAND",
    )
    telegram.add(
        BELGIUM_MAXIMUM_DEMAND_MONTH,
        MBusObject(
            (0, 0),
            [
                {"value": datetime.datetime.fromtimestamp(1551642218)},
                {"value": Decimal("4.11"), "unit": "kW"},
            ],
        ),
        "BELGIUM_MAXIMUM_DEMAND_MONTH",
    )
    telegram.add(
        MBUS_DEVICE_TYPE,
        CosemObject((0, 1), [{"value": "003", "unit": ""}]),
        "MBUS_DEVICE_TYPE",
    )
    telegram.add(
        MBUS_EQUIPMENT_IDENTIFIER,
        CosemObject(
            (0, 1),
            [{"value": "37464C4F32313139303333373331", "unit": ""}],
        ),
        "MBUS_EQUIPMENT_IDENTIFIER",
    )
    telegram.add(
        MBUS_METER_READING,
        MBusObject(
            (0, 1),
            [
                {"value": datetime.datetime.fromtimestamp(1551642213)},
                {"value": Decimal("745.695"), "unit": "m3"},
            ],
        ),
        "MBUS_METER_READING",
    )
    telegram.add(
        MBUS_DEVICE_TYPE,
        CosemObject((0, 2), [{"value": "007", "unit": ""}]),
        "MBUS_DEVICE_TYPE",
    )
    telegram.add(
        MBUS_EQUIPMENT_IDENTIFIER,
        CosemObject(
            (0, 2),
            [{"value": "37464C4F32313139303333373332", "unit": ""}],
        ),
        "MBUS_EQUIPMENT_IDENTIFIER",
    )
    telegram.add(
        MBUS_METER_READING,
        MBusObject(
            (0, 2),
            [
                {"value": datetime.datetime.fromtimestamp(1551642214)},
                {"value": Decimal("678.695"), "unit": "m3"},
            ],
        ),
        "MBUS_METER_READING",
    )
    telegram.add(
        MBUS_DEVICE_TYPE,
        CosemObject((0, 3), [{"value": "003", "unit": ""}]),
        "MBUS_DEVICE_TYPE",
    )
    telegram.add(
        MBUS_EQUIPMENT_IDENTIFIER,
        CosemObject(
            (0, 3),
            [{"value": "37464C4F32313139303333373333", "unit": ""}],
        ),
        "MBUS_EQUIPMENT_IDENTIFIER",
    )
    telegram.add(
        MBUS_METER_READING,
        MBusObject(
            (0, 3),
            [
                {"value": datetime.datetime.fromtimestamp(1551642215)},
                {"value": Decimal("12.12"), "unit": "m3"},
            ],
        ),
        "MBUS_METER_READING",
    )
    telegram.add(
        MBUS_DEVICE_TYPE,
        CosemObject((0, 4), [{"value": "007", "unit": ""}]),
        "MBUS_DEVICE_TYPE",
    )
    telegram.add(
        MBUS_EQUIPMENT_IDENTIFIER,
        CosemObject(
            (0, 4),
            [{"value": "37464C4F32313139303333373334", "unit": ""}],
        ),
        "MBUS_EQUIPMENT_IDENTIFIER",
    )
    telegram.add(
        MBUS_METER_READING,
        MBusObject(
            (0, 4),
            [
                {"value": datetime.datetime.fromtimestamp(1551642216)},
                {"value": Decimal("13.13"), "unit": "m3"},
            ],
        ),
        "MBUS_METER_READING",
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
    assert active_tariff.state == "normal"
    assert active_tariff.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENUM
    assert active_tariff.attributes.get(ATTR_OPTIONS) == ["low", "normal"]
    assert active_tariff.attributes.get(ATTR_STATE_CLASS) is None
    assert active_tariff.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None

    # check current average demand is parsed correctly
    avg_demand = hass.states.get("sensor.electricity_meter_current_average_demand")
    assert avg_demand.state == "1.75"
    assert avg_demand.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.KILO_WATT
    assert avg_demand.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    # check max average demand is parsed correctly
    max_demand = hass.states.get(
        "sensor.electricity_meter_maximum_demand_current_month"
    )
    assert max_demand.state == "4.11"
    assert max_demand.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.KILO_WATT
    assert max_demand.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    # check if gas consumption mbus1 is parsed correctly
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

    # check if water usage mbus2 is parsed correctly
    water_consumption = hass.states.get("sensor.water_meter_water_consumption")
    assert water_consumption.state == "678.695"
    assert (
        water_consumption.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.WATER
    )
    assert (
        water_consumption.attributes.get(ATTR_STATE_CLASS)
        == SensorStateClass.TOTAL_INCREASING
    )
    assert (
        water_consumption.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfVolume.CUBIC_METERS
    )

    # check if gas consumption mbus1 is parsed correctly
    gas_consumption = hass.states.get("sensor.gas_meter_gas_consumption_2")
    assert gas_consumption.state == "12.12"
    assert gas_consumption.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.GAS
    assert (
        gas_consumption.attributes.get(ATTR_STATE_CLASS)
        == SensorStateClass.TOTAL_INCREASING
    )
    assert (
        gas_consumption.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfVolume.CUBIC_METERS
    )

    # check if water usage mbus2 is parsed correctly
    water_consumption = hass.states.get("sensor.water_meter_water_consumption_2")
    assert water_consumption.state == "13.13"
    assert (
        water_consumption.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.WATER
    )
    assert (
        water_consumption.attributes.get(ATTR_STATE_CLASS)
        == SensorStateClass.TOTAL_INCREASING
    )
    assert (
        water_consumption.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfVolume.CUBIC_METERS
    )