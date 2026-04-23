async def test_on_remote_control_paired(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    device_registry: DeviceRegistry,
    entity_registry: EntityRegistry,
    mock_config_entry: MockConfigEntry,
    mock_mozart_client: AsyncMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that the integration reloads when a new remote has been paired."""

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    # Check device and API call count
    assert mock_mozart_client.get_bluetooth_remotes.call_count == 3
    assert device_registry.async_get_device({(DOMAIN, TEST_REMOTE_SERIAL_PAIRED)})

    # Check number of entities (button and remote events and media_player)
    assert list(entity_registry.entities.keys()) == unordered(
        [*get_balance_entity_ids(), *get_remote_entity_ids()]
    )
    # "Pair" a new remote
    mock_mozart_client.get_bluetooth_remotes.return_value = PairedRemoteResponse(
        items=[
            # Already paired
            PairedRemote(
                address="",
                app_version="1.0.0",
                battery_level=50,
                connected=True,
                serial_number=TEST_REMOTE_SERIAL,
                name="BEORC",
            ),
            # Not paired yet
            PairedRemote(
                address="",
                app_version="1.0.0",
                battery_level=50,
                connected=True,
                serial_number="66666666",
                name="BEORC",
            ),
        ]
    )
    remote_callback = mock_mozart_client.get_notification_notifications.call_args[0][0]

    # Trigger the notification
    await remote_callback(
        WebsocketNotificationTag(
            value=WebsocketNotification.REMOTE_CONTROL_DEVICES.value
        )
    )
    await hass.async_block_till_done()

    # Check device and API call count
    assert mock_mozart_client.get_bluetooth_remotes.call_count == 8
    assert device_registry.async_get_device({(DOMAIN, TEST_REMOTE_SERIAL_PAIRED)})
    assert device_registry.async_get_device(
        {(DOMAIN, f"66666666_{TEST_SERIAL_NUMBER}")}
    )

    # Check logger
    assert (
        f"A Beoremote One has been paired or unpaired to {mock_config_entry.title}. Reloading config entry to add device and entities"
        in caplog.text
    )

    # Check number of entities (remote and button events and media_player)
    entity_ids_available = list(entity_registry.entities.keys())

    assert entity_ids_available == unordered(
        [
            *get_balance_entity_ids(),
            *get_remote_entity_ids(),
            *get_remote_entity_ids("66666666"),
        ]
    )
    assert entity_ids_available == snapshot