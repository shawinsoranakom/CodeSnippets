async def test_slots_switch_turn_off_turn_on(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test send turn on and off for a switch with slots."""
    device = get_device("Gaming room")
    mock_setup = await device.setup_entry(hass)

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, mock_setup.entry.unique_id)}
    )
    entries = er.async_entries_for_device(entity_registry, device_entry.id)
    switches = [entry for entry in entries if entry.domain == Platform.SWITCH]
    assert len(switches) == 4

    for switch in switches:
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {"entity_id": switch.entity_id},
            blocking=True,
        )
        assert hass.states.get(switch.entity_id).state == STATE_OFF

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {"entity_id": switch.entity_id},
            blocking=True,
        )
        assert hass.states.get(switch.entity_id).state == STATE_ON

        assert mock_setup.api.auth.call_count == 1