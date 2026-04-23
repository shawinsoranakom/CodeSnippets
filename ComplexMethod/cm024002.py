async def test_integration_multiple_entity_platforms(hass: HomeAssistant) -> None:
    """Test integration of PassiveBluetoothProcessorCoordinator with multiple platforms."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    @callback
    def _mock_update_method(
        service_info: BluetoothServiceInfo,
    ) -> dict[str, str]:
        return {"test": "data"}

    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        "aa:bb:cc:dd:ee:ff",
        BluetoothScanningMode.ACTIVE,
        _mock_update_method,
    )
    assert coordinator.available is False  # no data yet

    binary_sensor_processor = PassiveBluetoothDataProcessor(
        lambda service_info: BINARY_SENSOR_PASSIVE_BLUETOOTH_DATA_UPDATE
    )
    sensor_processor = PassiveBluetoothDataProcessor(
        lambda service_info: SENSOR_PASSIVE_BLUETOOTH_DATA_UPDATE
    )

    coordinator.async_register_processor(binary_sensor_processor)
    coordinator.async_register_processor(sensor_processor)
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