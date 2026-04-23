async def test_integration_multiple_entity_platforms_with_reload_and_restart(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test integration of PassiveBluetoothProcessorCoordinator with multiple platforms with reload."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    entry = MockConfigEntry(domain=DOMAIN, data={})

    @callback
    def _mock_update_method(
        service_info: BluetoothServiceInfo,
    ) -> dict[str, str]:
        return {"test": "data"}

    current_entry.set(entry)
    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        "aa:bb:cc:dd:ee:ff",
        BluetoothScanningMode.ACTIVE,
        _mock_update_method,
    )
    assert coordinator.available is False  # no data yet

    binary_sensor_processor = PassiveBluetoothDataProcessor(
        lambda service_info: BINARY_SENSOR_PASSIVE_BLUETOOTH_DATA_UPDATE,
        BINARY_SENSOR_DOMAIN,
    )
    sensor_processor = PassiveBluetoothDataProcessor(
        lambda service_info: SENSOR_PASSIVE_BLUETOOTH_DATA_UPDATE, SENSOR_DOMAIN
    )

    unregister_binary_sensor_processor = coordinator.async_register_processor(
        binary_sensor_processor, BinarySensorEntityDescription
    )
    unregister_sensor_processor = coordinator.async_register_processor(
        sensor_processor, SensorEntityDescription
    )
    cancel_coordinator = coordinator.async_start()

    binary_sensor_processor.async_add_listener(MagicMock())
    sensor_processor.async_add_listener(MagicMock())

    mock_add_sensor_entities = MagicMock()
    mock_add_binary_sensor_entities = MagicMock()

    sensor_processor.async_add_entities_listener(
        PassiveBluetoothProcessorEntity,
        mock_add_sensor_entities,
    )
    binary_sensor_processor.async_add_entities_listener(
        PassiveBluetoothProcessorEntity,
        mock_add_binary_sensor_entities,
    )

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)
    # First call with just the remote sensor entities results in them being added
    assert len(mock_add_binary_sensor_entities.mock_calls) == 1
    assert len(mock_add_sensor_entities.mock_calls) == 1

    binary_sensor_entities = [
        *mock_add_binary_sensor_entities.mock_calls[0][1][0],
    ]
    sensor_entities = [
        *mock_add_sensor_entities.mock_calls[0][1][0],
    ]

    sensor_entity_one: PassiveBluetoothProcessorEntity = sensor_entities[0]
    sensor_entity_one.hass = hass
    assert sensor_entity_one.available is True
    assert sensor_entity_one.unique_id == "aa:bb:cc:dd:ee:ff-pressure"
    assert sensor_entity_one.device_info == {
        "identifiers": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
        "connections": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
        "manufacturer": "Test Manufacturer",
        "model": "Test Model",
        "name": "Test Device",
    }
    assert sensor_entity_one.entity_key == PassiveBluetoothEntityKey(
        key="pressure", device_id=None
    )

    binary_sensor_entity_one: PassiveBluetoothProcessorEntity = binary_sensor_entities[
        0
    ]
    binary_sensor_entity_one.hass = hass
    assert binary_sensor_entity_one.available is True
    assert binary_sensor_entity_one.unique_id == "aa:bb:cc:dd:ee:ff-motion"
    assert binary_sensor_entity_one.device_info == {
        "identifiers": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
        "connections": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
        "manufacturer": "Test Manufacturer",
        "model": "Test Model",
        "name": "Test Device",
    }
    assert binary_sensor_entity_one.entity_key == PassiveBluetoothEntityKey(
        key="motion", device_id=None
    )
    cancel_coordinator()
    unregister_binary_sensor_processor()
    unregister_sensor_processor()

    mock_add_sensor_entities = MagicMock()
    mock_add_binary_sensor_entities = MagicMock()

    current_entry.set(entry)
    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        "aa:bb:cc:dd:ee:ff",
        BluetoothScanningMode.ACTIVE,
        _mock_update_method,
    )
    binary_sensor_processor = PassiveBluetoothDataProcessor(
        lambda service_info: DEVICE_ONLY_PASSIVE_BLUETOOTH_DATA_UPDATE,
        BINARY_SENSOR_DOMAIN,
    )
    sensor_processor = PassiveBluetoothDataProcessor(
        lambda service_info: DEVICE_ONLY_PASSIVE_BLUETOOTH_DATA_UPDATE,
        SENSOR_DOMAIN,
    )

    sensor_processor.async_add_entities_listener(
        PassiveBluetoothProcessorEntity,
        mock_add_sensor_entities,
    )
    binary_sensor_processor.async_add_entities_listener(
        PassiveBluetoothProcessorEntity,
        mock_add_binary_sensor_entities,
    )

    unregister_binary_sensor_processor = coordinator.async_register_processor(
        binary_sensor_processor, BinarySensorEntityDescription
    )
    unregister_sensor_processor = coordinator.async_register_processor(
        sensor_processor, SensorEntityDescription
    )
    cancel_coordinator = coordinator.async_start()

    assert len(mock_add_binary_sensor_entities.mock_calls) == 1
    assert len(mock_add_sensor_entities.mock_calls) == 1

    binary_sensor_entities = [
        *mock_add_binary_sensor_entities.mock_calls[0][1][0],
    ]
    sensor_entities = [
        *mock_add_sensor_entities.mock_calls[0][1][0],
    ]

    sensor_entity_one: PassiveBluetoothProcessorEntity = sensor_entities[0]
    sensor_entity_one.hass = hass
    assert sensor_entity_one.available is True
    assert sensor_entity_one.unique_id == "aa:bb:cc:dd:ee:ff-pressure"
    assert sensor_entity_one.device_info == {
        "identifiers": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
        "connections": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
        "manufacturer": "Test Manufacturer",
        "model": "Test Model",
        "name": "Test Device",
    }
    assert sensor_entity_one.entity_key == PassiveBluetoothEntityKey(
        key="pressure", device_id=None
    )

    binary_sensor_entity_one: PassiveBluetoothProcessorEntity = binary_sensor_entities[
        0
    ]
    binary_sensor_entity_one.hass = hass
    assert binary_sensor_entity_one.available is True
    assert binary_sensor_entity_one.unique_id == "aa:bb:cc:dd:ee:ff-motion"
    assert binary_sensor_entity_one.device_info == {
        "identifiers": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
        "connections": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
        "manufacturer": "Test Manufacturer",
        "model": "Test Model",
        "name": "Test Device",
    }
    assert binary_sensor_entity_one.entity_key == PassiveBluetoothEntityKey(
        key="motion", device_id=None
    )

    await hass.async_stop()
    await hass.async_block_till_done()

    assert SENSOR_DOMAIN in hass_storage[STORAGE_KEY]["data"][entry.entry_id]
    assert BINARY_SENSOR_DOMAIN in hass_storage[STORAGE_KEY]["data"][entry.entry_id]

    # We don't normally cancel or unregister these at stop,
    # but since we are mocking a restart we need to cleanup
    cancel_coordinator()
    unregister_binary_sensor_processor()
    unregister_sensor_processor()

    async with async_test_home_assistant() as test_hass:
        await async_setup_component(test_hass, DOMAIN, {DOMAIN: {}})

        current_entry.set(entry)
        coordinator = PassiveBluetoothProcessorCoordinator(
            test_hass,
            _LOGGER,
            "aa:bb:cc:dd:ee:ff",
            BluetoothScanningMode.ACTIVE,
            _mock_update_method,
        )
        assert coordinator.available is False  # no data yet

        mock_add_sensor_entities = MagicMock()
        mock_add_binary_sensor_entities = MagicMock()

        binary_sensor_processor = PassiveBluetoothDataProcessor(
            lambda service_info: DEVICE_ONLY_PASSIVE_BLUETOOTH_DATA_UPDATE,
            BINARY_SENSOR_DOMAIN,
        )
        sensor_processor = PassiveBluetoothDataProcessor(
            lambda service_info: DEVICE_ONLY_PASSIVE_BLUETOOTH_DATA_UPDATE,
            SENSOR_DOMAIN,
        )

        sensor_processor.async_add_entities_listener(
            PassiveBluetoothProcessorEntity,
            mock_add_sensor_entities,
        )
        binary_sensor_processor.async_add_entities_listener(
            PassiveBluetoothProcessorEntity,
            mock_add_binary_sensor_entities,
        )

        unregister_binary_sensor_processor = coordinator.async_register_processor(
            binary_sensor_processor, BinarySensorEntityDescription
        )
        unregister_sensor_processor = coordinator.async_register_processor(
            sensor_processor, SensorEntityDescription
        )
        cancel_coordinator = coordinator.async_start()

        assert len(mock_add_binary_sensor_entities.mock_calls) == 1
        assert len(mock_add_sensor_entities.mock_calls) == 1

        binary_sensor_entities = [
            *mock_add_binary_sensor_entities.mock_calls[0][1][0],
        ]
        sensor_entities = [
            *mock_add_sensor_entities.mock_calls[0][1][0],
        ]

        sensor_entity_one: PassiveBluetoothProcessorEntity = sensor_entities[0]
        sensor_entity_one.hass = test_hass
        assert sensor_entity_one.available is False  # service data not injected
        assert sensor_entity_one.unique_id == "aa:bb:cc:dd:ee:ff-pressure"
        assert sensor_entity_one.device_info == {
            "identifiers": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
            "connections": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
            "manufacturer": "Test Manufacturer",
            "model": "Test Model",
            "name": "Test Device",
        }
        assert sensor_entity_one.entity_key == PassiveBluetoothEntityKey(
            key="pressure", device_id=None
        )

        binary_sensor_entity_one: PassiveBluetoothProcessorEntity = (
            binary_sensor_entities[0]
        )
        binary_sensor_entity_one.hass = test_hass
        assert binary_sensor_entity_one.available is False  # service data not injected
        assert binary_sensor_entity_one.unique_id == "aa:bb:cc:dd:ee:ff-motion"
        assert binary_sensor_entity_one.device_info == {
            "identifiers": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
            "connections": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
            "manufacturer": "Test Manufacturer",
            "model": "Test Model",
            "name": "Test Device",
        }
        assert binary_sensor_entity_one.entity_key == PassiveBluetoothEntityKey(
            key="motion", device_id=None
        )
        cancel_coordinator()
        unregister_binary_sensor_processor()
        unregister_sensor_processor()
        await test_hass.async_stop()