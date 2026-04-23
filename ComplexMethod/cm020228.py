async def test_migration_device_online_end_to_end_ignores_other_devices(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test migration from single config entry."""
    legacy_config_entry = MockConfigEntry(
        domain=DOMAIN, title="LEGACY", data={}, unique_id=DOMAIN
    )
    legacy_config_entry.add_to_hass(hass)

    other_domain_config_entry = MockConfigEntry(
        domain="other_domain", data={}, unique_id="other_domain"
    )
    other_domain_config_entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=legacy_config_entry.entry_id,
        identifiers={(DOMAIN, SERIAL)},
        connections={(dr.CONNECTION_NETWORK_MAC, MAC_ADDRESS)},
        name=LABEL,
    )
    other_device = device_registry.async_get_or_create(
        config_entry_id=other_domain_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "556655665566")},
        name=LABEL,
    )
    light_entity_reg = entity_registry.async_get_or_create(
        config_entry=legacy_config_entry,
        platform=DOMAIN,
        domain="light",
        unique_id=SERIAL,
        original_name=LABEL,
        device_id=device.id,
    )
    ignored_entity_reg = entity_registry.async_get_or_create(
        config_entry=other_domain_config_entry,
        platform=DOMAIN,
        domain="sensor",
        unique_id="00:00:00:00:00:00_sensor",
        original_name=LABEL,
        device_id=device.id,
    )
    garbage_entity_reg = entity_registry.async_get_or_create(
        config_entry=legacy_config_entry,
        platform=DOMAIN,
        domain="sensor",
        unique_id="garbage",
        original_name=LABEL,
        device_id=other_device.id,
    )

    with _patch_discovery(), _patch_config_flow_try_connect(), _patch_device():
        await setup.async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=20))
        await hass.async_block_till_done()

        new_entry = None
        legacy_entry = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.unique_id == DOMAIN:
                legacy_entry = entry
            else:
                new_entry = entry

        assert new_entry is not None
        assert legacy_entry is None

        assert device.config_entries == {legacy_config_entry.entry_id}
        assert light_entity_reg.config_entry_id == legacy_config_entry.entry_id
        assert ignored_entity_reg.config_entry_id == other_domain_config_entry.entry_id
        assert garbage_entity_reg.config_entry_id == legacy_config_entry.entry_id

        assert (
            er.async_entries_for_config_entry(entity_registry, legacy_config_entry)
            == []
        )
        assert (
            dr.async_entries_for_config_entry(device_registry, legacy_config_entry)
            == []
        )