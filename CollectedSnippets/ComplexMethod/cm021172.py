async def test_cover_device_association(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test the cover entity device association."""

    entity_entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert len(entity_entries) >= 1

    for entry in entity_entries:
        assert entry.device_id is not None
        device_entry = device_registry.async_get(entry.device_id)
        assert device_entry is not None

        # For dual roller shutters, the unique_id is suffixed with "_upper" or "_lower",
        # so remove that suffix to get the domain_id for device registry lookup
        domain_id = entry.unique_id
        if entry.unique_id.endswith("_upper") or entry.unique_id.endswith("_lower"):
            domain_id = entry.unique_id.rsplit("_", 1)[0]
        assert (DOMAIN, domain_id) in device_entry.identifiers
        assert device_entry.via_device_id is not None
        via_device_entry = device_registry.async_get(device_entry.via_device_id)
        assert via_device_entry is not None
        assert (
            DOMAIN,
            f"gateway_{mock_config_entry.entry_id}",
        ) in via_device_entry.identifiers