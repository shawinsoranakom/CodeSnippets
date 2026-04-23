async def test_on_remote_control_already_added(
    hass: HomeAssistant,
    device_registry: DeviceRegistry,
    entity_registry: EntityRegistry,
    mock_config_entry: MockConfigEntry,
    mock_mozart_client: AsyncMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that the integration does nothing when a remote that already has a device triggers a check."""

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    # Check device and API call count
    assert mock_mozart_client.get_bluetooth_remotes.call_count == 3
    assert device_registry.async_get_device({(DOMAIN, TEST_REMOTE_SERIAL_PAIRED)})

    # Check number of entities (remote and button events and media_player)
    assert list(entity_registry.entities.keys()) == unordered(
        [*get_balance_entity_ids(), *get_remote_entity_ids()]
    )
    remote_callback = mock_mozart_client.get_notification_notifications.call_args[0][0]

    # Trigger the notification
    await remote_callback(
        WebsocketNotificationTag(
            value=WebsocketNotification.REMOTE_CONTROL_DEVICES.value
        )
    )

    await hass.async_block_till_done()

    # Check device and API call count (triggered once by the WebSocket notification)
    assert mock_mozart_client.get_bluetooth_remotes.call_count == 4
    assert device_registry.async_get_device({(DOMAIN, TEST_REMOTE_SERIAL_PAIRED)})

    # Check number of entities (remote and button events and media_player)
    entity_ids_available = list(entity_registry.entities.keys())

    assert list(entity_registry.entities.keys()) == unordered(
        [*get_balance_entity_ids(), *get_remote_entity_ids()]
    )
    assert entity_ids_available == snapshot