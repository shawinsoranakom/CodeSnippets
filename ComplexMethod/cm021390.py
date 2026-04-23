async def test_remote_setup_works(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test a successful setup with all remotes."""
    for device in map(get_device, REMOTE_DEVICES):
        mock_setup = await device.setup_entry(hass)

        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, mock_setup.entry.unique_id)}
        )
        entries = er.async_entries_for_device(entity_registry, device_entry.id)
        remotes = [entry for entry in entries if entry.domain == Platform.REMOTE]
        assert len(remotes) == 1

        remote = remotes[0]
        assert (
            hass.states.get(remote.entity_id).attributes[ATTR_FRIENDLY_NAME]
            == device.name
        )
        assert hass.states.get(remote.entity_id).state == STATE_ON
        assert mock_setup.api.auth.call_count == 1