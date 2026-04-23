async def test_integration_with_entity_without_a_device(hass: HomeAssistant) -> None:
    """Test integration with PassiveBluetoothCoordinatorEntity with no device."""
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
        return NO_DEVICES_PASSIVE_BLUETOOTH_DATA_UPDATE

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

    mock_add_entities = MagicMock()

    processor.async_add_entities_listener(
        PassiveBluetoothProcessorEntity,
        mock_add_entities,
    )

    inject_bluetooth_service_info(hass, NO_DEVICES_BLUETOOTH_SERVICE_INFO)
    # First call with just the remote sensor entities results in them being added
    assert len(mock_add_entities.mock_calls) == 1

    inject_bluetooth_service_info(hass, NO_DEVICES_BLUETOOTH_SERVICE_INFO_2)
    # Second call with just the remote sensor entities does not add them again
    assert len(mock_add_entities.mock_calls) == 1

    entities = mock_add_entities.mock_calls[0][1][0]
    entity_one: PassiveBluetoothProcessorEntity = entities[0]
    entity_one.hass = hass
    assert entity_one.available is True
    assert entity_one.unique_id == "aa:bb:cc:dd:ee:ff-temperature"
    assert entity_one.device_info == {
        "identifiers": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
        "connections": {("bluetooth", "aa:bb:cc:dd:ee:ff")},
        "name": "Generic",
    }
    assert entity_one.entity_key == PassiveBluetoothEntityKey(
        key="temperature", device_id=None
    )
    cancel_coordinator()