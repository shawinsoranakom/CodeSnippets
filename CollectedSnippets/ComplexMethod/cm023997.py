async def test_async_set_updated_data_usage(hass: HomeAssistant) -> None:
    """Test async_set_updated_data of the PassiveBluetoothProcessorCoordinator."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

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
        assert data == {"test": "data"}
        return GENERIC_PASSIVE_BLUETOOTH_DATA_UPDATE

    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        "aa:bb:cc:dd:ee:ff",
        BluetoothScanningMode.ACTIVE,
        _mock_update_method,
    )
    assert coordinator.available is False  # no data yet

    processor = PassiveBluetoothDataProcessor(_async_generate_mock_data)

    unregister_processor = coordinator.async_register_processor(processor)
    cancel_coordinator = coordinator.async_start()

    entity_key = PassiveBluetoothEntityKey("temperature", None)
    entity_key_events = []
    all_events = []
    mock_entity = MagicMock()
    mock_add_entities = MagicMock()

    def _async_entity_key_listener(data: PassiveBluetoothDataUpdate | None) -> None:
        """Mock entity key listener."""
        entity_key_events.append(data)

    cancel_async_add_entity_key_listener = processor.async_add_entity_key_listener(
        _async_entity_key_listener,
        entity_key,
    )

    def _all_listener(data: PassiveBluetoothDataUpdate | None) -> None:
        """Mock an all listener."""
        all_events.append(data)

    cancel_listener = processor.async_add_listener(
        _all_listener,
    )

    cancel_async_add_entities_listener = processor.async_add_entities_listener(
        mock_entity,
        mock_add_entities,
    )

    assert coordinator.available is False
    coordinator.async_set_updated_data({"test": "data"})
    assert coordinator.available is True

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)

    # Each listener should receive the same data
    # since both match, and an additional all_events
    # for the async_set_updated_data call
    assert len(entity_key_events) == 1
    assert len(all_events) == 2

    # There should be 4 calls to create entities
    assert len(mock_entity.mock_calls) == 2

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO_2)

    # Only the all listener should receive the new data
    # since temperature is not in the new data, and an additional all_events
    # for the async_set_updated_data call
    assert len(entity_key_events) == 1
    assert len(all_events) == 3

    # On the second, the entities should already be created
    # so the mock should not be called again
    assert len(mock_entity.mock_calls) == 2

    cancel_async_add_entity_key_listener()
    cancel_listener()
    cancel_async_add_entities_listener()

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)

    # Each listener should not trigger any more now
    # that they were cancelled
    assert len(entity_key_events) == 1
    assert len(all_events) == 3
    assert len(mock_entity.mock_calls) == 2
    assert coordinator.available is True

    unregister_processor()
    cancel_coordinator()