async def test_setup_through_bluetooth_only(
    hass: HomeAssistant,
    mock_config_entry_bluetooth: MockConfigEntry,
    mock_lamarzocco_bluetooth: MagicMock,
    mock_ble_device_from_address: MagicMock,
    mock_cloud_client: MagicMock,
    device_registry: dr.DeviceRegistry,
    device_fixture: ModelName,
    entities: list[tuple[str, str]],
    snapshot: SnapshotAssertion,
) -> None:
    """Test we can setup without a cloud connection."""

    # Simulate cloud connection failures
    mock_cloud_client.get_thing_settings.side_effect = RequestNotSuccessful("")
    mock_cloud_client.async_get_access_token.side_effect = RequestNotSuccessful("")
    mock_lamarzocco_bluetooth.get_dashboard.side_effect = RequestNotSuccessful("")
    mock_lamarzocco_bluetooth.get_coffee_and_flush_counter.side_effect = (
        RequestNotSuccessful("")
    )
    mock_lamarzocco_bluetooth.get_schedule.side_effect = RequestNotSuccessful("")
    mock_lamarzocco_bluetooth.get_settings.side_effect = RequestNotSuccessful("")

    await async_init_integration(hass, mock_config_entry_bluetooth)
    assert mock_config_entry_bluetooth.state is ConfigEntryState.LOADED

    # Check all Bluetooth entities are available
    for entity_id in entities:
        entity = build_entity_id(
            entity_id[0], mock_lamarzocco_bluetooth.serial_number, entity_id[1]
        )
        state = hass.states.get(entity)
        assert state
        assert state.state != STATE_UNAVAILABLE
        assert state == snapshot(name=entity)

    # snapshot device
    device = device_registry.async_get_device(
        {(DOMAIN, mock_lamarzocco_bluetooth.serial_number)}
    )
    assert device
    assert device == snapshot(
        name=f"device_bluetooth_{mock_lamarzocco_bluetooth.serial_number}"
    )