async def test_remote_send_command(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test sending a command with all remotes."""
    for device in map(get_device, REMOTE_DEVICES):
        mock_setup = await device.setup_entry(hass)

        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, mock_setup.entry.unique_id)}
        )
        entries = er.async_entries_for_device(entity_registry, device_entry.id)
        remotes = [entry for entry in entries if entry.domain == Platform.REMOTE]
        assert len(remotes) == 1

        remote = remotes[0]
        await hass.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_SEND_COMMAND,
            {"entity_id": remote.entity_id, "command": "b64:" + IR_PACKET},
            blocking=True,
        )

        assert mock_setup.api.send_data.call_count == 1
        assert mock_setup.api.send_data.call_args == call(b64decode(IR_PACKET))
        assert mock_setup.api.auth.call_count == 1