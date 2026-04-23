async def test_integration_with_entity(hass: HomeAssistant) -> None:
    """Test integration of PassiveBluetoothProcessorCoordinator with PassiveBluetoothCoordinatorEntity."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    update_count = 0

    @callback
    def _mock_update_method(
        service_info: BluetoothServiceInfo,
    ) -> dict[str, str]:
        return {"test": "data"}

    @callback
    def _async_generate_mock_data(
        data: dict[str, str],
    ) -> PassiveBluetoothDataUpdate:
        """Generate mock data."""
        nonlocal update_count
        update_count += 1
        if update_count > 2:
            return GOVEE_B5178_PRIMARY_AND_REMOTE_PASSIVE_BLUETOOTH_DATA_UPDATE
        return GOVEE_B5178_REMOTE_PASSIVE_BLUETOOTH_DATA_UPDATE

    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        "aa:bb:cc:dd:ee:ff",
        BluetoothScanningMode.ACTIVE,
        _mock_update_method,
    )
    assert coordinator.available is False  # no data yet

    processor = PassiveBluetoothDataProcessor(_async_generate_mock_data)

    coordinator.async_register_processor(processor)
    cancel_coordinator = coordinator.async_start()

    processor.async_add_listener(MagicMock())

    mock_add_entities = MagicMock()

    processor.async_add_entities_listener(
        PassiveBluetoothProcessorEntity,
        mock_add_entities,
    )

    entity_key_events = []

    def _async_entity_key_listener(data: PassiveBluetoothDataUpdate | None) -> None:
        """Mock entity key listener."""
        entity_key_events.append(data)

    cancel_async_add_entity_key_listener = processor.async_add_entity_key_listener(
        _async_entity_key_listener,
        PassiveBluetoothEntityKey(key="humidity", device_id="primary"),
    )

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)
    # First call with just the remote sensor entities results in them being added
    assert len(mock_add_entities.mock_calls) == 1

    # should have triggered the entity key listener since the
    # the device is becoming available
    assert len(entity_key_events) == 1

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO_2)
    # Second call with just the remote sensor entities does not add them again
    assert len(mock_add_entities.mock_calls) == 1

    # should not have triggered the entity key listener since there
    # there is no update with the entity key
    assert len(entity_key_events) == 1

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)
    # Third call with primary and remote sensor entities adds the primary sensor entities
    assert len(mock_add_entities.mock_calls) == 2

    # should not have triggered the entity key listener since there
    # there is an update with the entity key
    assert len(entity_key_events) == 2

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO_2)
    # Forth call with both primary and remote sensor entities does not add them again
    assert len(mock_add_entities.mock_calls) == 2

    # should not have triggered the entity key listener humidity
    # is not in the update
    assert len(entity_key_events) == 2

    entities = [
        *mock_add_entities.mock_calls[0][1][0],
        *mock_add_entities.mock_calls[1][1][0],
    ]

    entity_one: PassiveBluetoothProcessorEntity = entities[0]
    entity_one.hass = hass
    assert entity_one.available is True
    assert entity_one.unique_id == "aa:bb:cc:dd:ee:ff-temperature-remote"
    assert entity_one.device_info == {
        "identifiers": {("bluetooth", "aa:bb:cc:dd:ee:ff-remote")},
        "manufacturer": "Govee",
        "model": "H5178-REMOTE",
        "name": "B5178D6FB Remote",
    }
    assert entity_one.entity_key == PassiveBluetoothEntityKey(
        key="temperature", device_id="remote"
    )
    cancel_async_add_entity_key_listener()
    cancel_coordinator()