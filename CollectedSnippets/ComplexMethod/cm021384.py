async def test_slots_switch_setup_works(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test a successful setup with a switch with slots."""
    device = get_device("Gaming room")
    mock_setup = await device.setup_entry(hass)

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, mock_setup.entry.unique_id)}
    )
    entries = er.async_entries_for_device(entity_registry, device_entry.id)
    switches = [entry for entry in entries if entry.domain == Platform.SWITCH]
    assert len(switches) == 4

    for slot, switch in enumerate(switches):
        assert (
            hass.states.get(switch.entity_id).attributes[ATTR_FRIENDLY_NAME]
            == f"{device.name} S{slot + 1}"
        )
        assert hass.states.get(switch.entity_id).state == STATE_OFF
        assert mock_setup.api.auth.call_count == 1