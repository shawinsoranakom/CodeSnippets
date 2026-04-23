async def test_migrate_from_future(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    target_domain: Platform,
) -> None:
    """Test migration."""
    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: "switch.test",
            CONF_TARGET_DOMAIN: target_domain,
        },
        title="ABC",
        version=2,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check migration was not successful and did not add invert option
    assert config_entry.state is ConfigEntryState.MIGRATION_ERROR
    assert config_entry.options == {
        CONF_ENTITY_ID: "switch.test",
        CONF_TARGET_DOMAIN: target_domain,
    }
    assert config_entry.version == 2
    assert config_entry.minor_version == 1

    # Check the state and entity registry entry are not present
    assert hass.states.get(f"{target_domain}.abc") is None
    assert entity_registry.async_get(f"{target_domain}.abc") is None