async def test_remote_turn_off_turn_on(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test we do not send commands if the remotes are off."""
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
            SERVICE_TURN_OFF,
            {"entity_id": remote.entity_id},
            blocking=True,
        )
        assert hass.states.get(remote.entity_id).state == STATE_OFF

        await hass.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_SEND_COMMAND,
            {"entity_id": remote.entity_id, "command": "b64:" + IR_PACKET},
            blocking=True,
        )
        assert mock_setup.api.send_data.call_count == 0

        await hass.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_TURN_ON,
            {"entity_id": remote.entity_id},
            blocking=True,
        )
        assert hass.states.get(remote.entity_id).state == STATE_ON

        await hass.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_SEND_COMMAND,
            {"entity_id": remote.entity_id, "command": "b64:" + IR_PACKET},
            blocking=True,
        )
        assert mock_setup.api.send_data.call_count == 1
        assert mock_setup.api.send_data.call_args == call(b64decode(IR_PACKET))
        assert mock_setup.api.auth.call_count == 1