async def test_migration_device_online_end_to_end(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test migration from single config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, title="LEGACY", data={}, unique_id=DOMAIN
    )
    config_entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, SERIAL)},
        connections={(dr.CONNECTION_NETWORK_MAC, MAC_ADDRESS)},
        name=LABEL,
    )
    light_entity_reg = entity_registry.async_get_or_create(
        config_entry=config_entry,
        platform=DOMAIN,
        domain="light",
        unique_id=dr.format_mac(SERIAL),
        original_name=LABEL,
        device_id=device.id,
    )

    with _patch_discovery(), _patch_config_flow_try_connect(), _patch_device():
        await setup.async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

        migrated_entry = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.unique_id == DOMAIN:
                migrated_entry = entry
                break

        assert migrated_entry is not None

        assert device.config_entries == {migrated_entry.entry_id}
        assert light_entity_reg.config_entry_id == migrated_entry.entry_id
        assert er.async_entries_for_config_entry(entity_registry, config_entry) == []

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=20))
        await hass.async_block_till_done()

        legacy_entry = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.unique_id == DOMAIN:
                legacy_entry = entry
                break

        assert legacy_entry is None