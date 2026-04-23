async def test_migrate_hourly_gas_to_mbus(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    dsmr_connection_fixture: tuple[MagicMock, MagicMock, MagicMock],
) -> None:
    """Test migration of unique_id."""
    (connection_factory, _transport, _protocol) = dsmr_connection_fixture

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="/dev/ttyUSB0",
        data={
            "port": "/dev/ttyUSB0",
            "dsmr_version": "5",
            "serial_id": "1234",
            "serial_id_gas": "4730303738353635363037343639323231",
        },
        options={
            "time_between_update": 0,
        },
    )

    mock_entry.add_to_hass(hass)

    old_unique_id = "4730303738353635363037343639323231_hourly_gas_meter_reading"

    device = device_registry.async_get_or_create(
        config_entry_id=mock_entry.entry_id,
        identifiers={(DOMAIN, mock_entry.entry_id)},
        name="Gas Meter",
    )
    await hass.async_block_till_done()

    entity: er.RegistryEntry = entity_registry.async_get_or_create(
        suggested_object_id="gas_meter_reading",
        disabled_by=None,
        domain=SENSOR_DOMAIN,
        platform=DOMAIN,
        device_id=device.id,
        unique_id=old_unique_id,
        config_entry=mock_entry,
    )
    assert entity.unique_id == old_unique_id
    await hass.async_block_till_done()

    telegram = Telegram()
    telegram.add(
        MBUS_DEVICE_TYPE,
        CosemObject((0, 1), [{"value": "003", "unit": ""}]),
        "MBUS_DEVICE_TYPE",
    )
    telegram.add(
        MBUS_EQUIPMENT_IDENTIFIER,
        CosemObject(
            (0, 1),
            [{"value": "4730303738353635363037343639323231", "unit": ""}],
        ),
        "MBUS_EQUIPMENT_IDENTIFIER",
    )
    telegram.add(
        MBUS_METER_READING,
        MBusObject(
            (0, 1),
            [
                {"value": datetime.datetime.fromtimestamp(1722749707)},
                {"value": Decimal("778.963"), "unit": "m3"},
            ],
        ),
        "MBUS_METER_READING",
    )

    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    telegram_callback = connection_factory.call_args_list[0][0][2]

    # simulate a telegram pushed from the smartmeter and parsed by dsmr_parser
    telegram_callback(telegram)

    # after receiving telegram entities need to have the chance to be created
    await hass.async_block_till_done()

    # Check a new device is created and the old device has been removed
    assert len(device_registry.devices) == 1
    assert not device_registry.async_get(device.id)
    new_entity = entity_registry.async_get("sensor.gas_meter_reading")
    new_device = device_registry.async_get(new_entity.device_id)
    new_dev_entities = er.async_entries_for_device(
        entity_registry, new_device.id, include_disabled_entities=True
    )
    assert new_dev_entities == [new_entity]

    # Check no entities are connected to the old device
    dev_entities = er.async_entries_for_device(
        entity_registry, device.id, include_disabled_entities=True
    )
    assert not dev_entities

    assert (
        entity_registry.async_get_entity_id(SENSOR_DOMAIN, DOMAIN, old_unique_id)
        is None
    )
    assert (
        entity_registry.async_get_entity_id(
            SENSOR_DOMAIN, DOMAIN, "4730303738353635363037343639323231"
        )
        == "sensor.gas_meter_reading"
    )